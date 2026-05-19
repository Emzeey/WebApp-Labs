import socket
import base64
import os
import sys

SERVER = "127.0.0.1"
PORT = 2525
BOUNDARY = "----=_MimeBoundaryLab6Python"

MIME_TYPES = {
    ".txt":  "text/plain",
    ".log":  "text/plain",
    ".csv":  "text/csv",
    ".html": "text/html",
    ".xml":  "text/xml",
    ".json": "application/json",
    ".pdf":  "application/pdf",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".bmp":  "image/bmp",
    ".webp": "image/webp",
    ".zip":  "application/zip",
}


def get_mime_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return MIME_TYPES.get(ext, "application/octet-stream")


def file_to_base64_lines(path: str) -> list[str]:
    """Zwraca zawartość pliku zakodowaną Base64 jako listę linii (max 76 znaków)."""
    with open(path, "rb") as f:
        raw = f.read()
    encoded = base64.b64encode(raw).decode()
    return [encoded[i:i+76] for i in range(0, len(encoded), 76)]


class SMTPClient:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def recv(self) -> str:
        buf = b""
        while True:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            buf += chunk
            lines = buf.decode(errors="replace").splitlines()
            if lines and len(lines[-1]) >= 4 and lines[-1][3] == " ":
                break
            if lines and len(lines[-1]) < 4:
                break
        resp = buf.decode(errors="replace").strip()
        print(f"<-- {resp}")
        return resp

    def send(self, line: str):
        print(f"--> {line}")
        self.sock.sendall((line + "\r\n").encode())

    def quit(self):
        self.send("QUIT")
        self.recv()
        self.sock.close()


def ask_recipients() -> list[str]:
    recipients = []
    print("Adresy odbiorców (pusty Enter = koniec):")
    while True:
        r = input(f"  Odbiorca {len(recipients)+1}: ").strip()
        if not r:
            if not recipients:
                print("  Podaj co najmniej jednego odbiorcę!")
                continue
            break
        recipients.append(r)
    return recipients


def ask_body() -> str:
    print("Treść wiadomości (dwa puste linie = koniec):")
    lines = []
    empty = 0
    while True:
        line = input()
        if line == "":
            empty += 1
            if empty >= 2:
                break
            lines.append("")
        else:
            empty = 0
            lines.append(line)
    return "\n".join(lines).rstrip()


def send_email_with_attachment(attachment_path: str, attachment_type: str):
    print("\n" + "=" * 60)
    if attachment_type == "text":
        print("  Zadanie 7 - Klient SMTP z załącznikiem tekstowym")
    else:
        print("  Zadanie 8 - Klient SMTP z załącznikiem obrazkowym")
    print("=" * 60)
    print()

    sender = input("Adres nadawcy (Enter = pas2017@interia.pl): ").strip()
    if not sender:
        sender = "pas2017@interia.pl"

    recipients = ask_recipients()
    subject = input("Temat: ").strip()
    body = ask_body()

    print("\nDane logowania:")
    login_user = input("  Login (Enter = pas2017@interia.pl): ").strip() or "pas2017@interia.pl"
    login_pass = input("  Haslo (Enter = P4SInf2017): ").strip() or "P4SInf2017"

    if not os.path.exists(attachment_path):
        print(f"[BŁĄD] Plik '{attachment_path}' nie istnieje!")
        return

    mime_type = get_mime_type(attachment_path)
    filename = os.path.basename(attachment_path)
    b64_lines = file_to_base64_lines(attachment_path)

    print(f"\n[Załącznik: {filename} | typ MIME: {mime_type} | rozmiar b64: {sum(len(l) for l in b64_lines)} znaków]")
    print(f"[Łączę z {SERVER}:{PORT}...]")

    try:
        c = SMTPClient(SERVER, PORT)
    except ConnectionRefusedError:
        print(f"[BŁĄD] Nie można połączyć z {SERVER}:{PORT}. Uruchom smtp_server.py!")
        return

    print("\n--- Sesja SMTP ---")
    c.recv()

    c.send("EHLO klient_zadania_7_8")
    c.recv()

    c.send("AUTH LOGIN")
    c.recv()
    c.send(base64.b64encode(login_user.encode()).decode())
    c.recv()
    c.send(base64.b64encode(login_pass.encode()).decode())
    resp = c.recv()

    if not resp.startswith("235"):
        print("[BŁĄD] Uwierzytelnienie nieudane!")
        c.quit()
        return

    c.send(f"MAIL FROM: <{sender}>")
    c.recv()

    for r in recipients:
        c.send(f"RCPT TO: <{r}>")
        c.recv()

    c.send("DATA")
    c.recv()

    c.send(f"From: <{sender}>")
    c.send(f"To: {', '.join(f'<{r}>' for r in recipients)}")
    c.send(f"Subject: {subject}")
    c.send("MIME-Version: 1.0")
    c.send(f'Content-Type: multipart/mixed; boundary="{BOUNDARY}"')
    c.send("")

    c.send(f"--{BOUNDARY}")
    c.send("Content-Type: text/plain; charset=utf-8")
    c.send("Content-Transfer-Encoding: 8bit")
    c.send("")
    for line in body.splitlines():
        c.send(line)
    c.send("")

    c.send(f"--{BOUNDARY}")
    c.send(f'Content-Type: {mime_type}; name="{filename}"')
    c.send(f'Content-Disposition: attachment; filename="{filename}"')
    c.send("Content-Transfer-Encoding: base64")
    c.send("")
    for line in b64_lines:
        c.send(line)
    c.send("")

    c.send(f"--{BOUNDARY}--")
    c.send(".")
    c.recv()

    c.quit()
    print(f"\n[OK] Wiadomość z załącznikiem '{filename}' wysłana!")


def main():
    if len(sys.argv) > 1:
        task = sys.argv[1]
    else:
        print("Wybierz zadanie:")
        print("  7 - Klient SMTP z załącznikiem tekstowym")
        print("  8 - Klient SMTP z załącznikiem obrazkowym")
        task = input("Twoj wybor (7/8): ").strip()

    if task == "7":
        default_path = "zalacznik.txt"
        path = input(f"Sciezka do pliku tekstowego (Enter = {default_path}): ").strip()
        if not path:
            path = default_path
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write("Przykladowy plik tekstowy do zadania 7.\n")
                    f.write("Protokol SMTP - Laboratorium 6\n")
                    f.write("Zawartosc zakodowana w Base64 (MIME).\n")
                print(f"[Utworzono przykładowy plik: {path}]")
        send_email_with_attachment(path, "text")

    elif task == "8":
        default_path = "obrazek.png"
        path = input(f"Sciezka do obrazka (Enter = {default_path}): ").strip()
        if not path:
            path = default_path
            if not os.path.exists(path):
                import struct, zlib

                def make_chunk(t, d):
                    c = t + d
                    return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

                w, h = 16, 16
                ihdr = make_chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                rows = b''.join(b'\x00' + bytes([0, i * 15, 255 - i * 15] * w) for i in range(h))
                idat = make_chunk(b'IDAT', zlib.compress(rows))
                iend = make_chunk(b'IEND', b'')
                png = b'\x89PNG\r\n\x1a\n' + ihdr + idat + iend
                with open(path, 'wb') as f:
                    f.write(png)
                print(f"[Utworzono przykładowy obrazek PNG: {path}]")
        send_email_with_attachment(path, "image")

    else:
        print(f"[BŁĄD] Nieznane zadanie: {task}. Podaj 7 lub 8.")


if __name__ == "__main__":
    main()
