#!/usr/bin/env python3
"""
Zadanie 10 - Serwer SMTP (symulacja)
Serwer działa na 127.0.0.1:2525 i obsługuje protokół SMTP.
Nie wysyła prawdziwych maili - symuluje działanie serwera.
"""

import socket
import threading
import base64
import datetime
import os

HOST = "127.0.0.1"
PORT = 2525
SAVED_MAILS_DIR = "received_mails"

# Przykładowe dane uwierzytelniające
USERS = {
    "pas2017@interia.pl": "P4SInf2017",
    "pasinf2017@interia.pl": "P4SInf2017",
    "test@localhost": "test123",
}


def save_email(session_data: dict):
    """Zapisuje odebrany e-mail do pliku."""
    os.makedirs(SAVED_MAILS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = os.path.join(SAVED_MAILS_DIR, f"mail_{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"Odebrano: {datetime.datetime.now()}\n")
        f.write(f"Od: {session_data.get('mail_from', '?')}\n")
        f.write(f"Do: {', '.join(session_data.get('rcpt_to', []))}\n")
        f.write("=" * 60 + "\n")
        f.write(session_data.get("data", "") + "\n")
    print(f"[SERWER] Zapisano e-mail: {filename}")
    return filename


def handle_client(conn: socket.socket, addr):
    """Obsługuje pojedyncze połączenie klienta SMTP."""
    print(f"[SERWER] Nowe połączenie od {addr}")

    session = {
        "authenticated": False,
        "mail_from": None,
        "rcpt_to": [],
        "data": "",
        "auth_step": None,   # None / "username" / "password"
        "auth_user": None,
    }

    def send(line: str):
        conn.sendall((line + "\r\n").encode())
        print(f"[S -> C] {line}")

    def recv_line() -> str:
        buf = b""
        while not buf.endswith(b"\n"):
            ch = conn.recv(1)
            if not ch:
                break
            buf += ch
        line = buf.decode(errors="replace").rstrip("\r\n")
        if line:
            print(f"[C -> S] {line}")
        return line

    # Powitanie
    send("220 localhost ESMTP PythonMailServer ready")

    try:
        while True:
            line = recv_line()
            if not line:
                break

            cmd = line.strip().upper()
            cmd_word = cmd.split()[0] if cmd else ""

            # ── EHLO / HELO ──────────────────────────────────────────────
            if cmd_word in ("EHLO", "HELO"):
                domain = line.split(maxsplit=1)[1] if len(line.split()) > 1 else "unknown"
                if cmd_word == "EHLO":
                    send(f"250-localhost Hello {domain}")
                    send("250-PIPELINING")
                    send("250-SIZE 52428800")
                    send("250-AUTH PLAIN LOGIN")
                    send("250-AUTH=PLAIN LOGIN")
                    send("250 8BITMIME")
                else:
                    send(f"250 localhost Hello {domain}")

            # ── AUTH LOGIN ────────────────────────────────────────────────
            elif cmd_word == "AUTH":
                parts = line.split()
                method = parts[1].upper() if len(parts) > 1 else ""

                if method == "LOGIN":
                    session["auth_step"] = "username"
                    # "Username:"
                    send("334 " + base64.b64encode(b"Username:").decode())

                elif method == "PLAIN":
                    # AUTH PLAIN <base64(authzid\0authcid\0passwd)>
                    if len(parts) > 2:
                        try:
                            decoded = base64.b64decode(parts[2]).split(b"\x00")
                            user = decoded[-2].decode()
                            passwd = decoded[-1].decode()
                            if USERS.get(user) == passwd:
                                session["authenticated"] = True
                                session["auth_user"] = user
                                send("235 2.7.0 Authentication successful")
                            else:
                                send("535 5.7.8 Authentication credentials invalid")
                        except Exception:
                            send("501 5.5.2 Cannot decode credentials")
                    else:
                        send("334 ")  # poproś o credentials
                else:
                    send("504 5.7.4 Unrecognized authentication type")

            # ── obsługa kroków AUTH LOGIN ─────────────────────────────────
            elif session["auth_step"] == "username":
                try:
                    session["auth_user"] = base64.b64decode(line).decode()
                except Exception:
                    session["auth_user"] = line
                session["auth_step"] = "password"
                # "Password:"
                send("334 " + base64.b64encode(b"Password:").decode())

            elif session["auth_step"] == "password":
                try:
                    password = base64.b64decode(line).decode()
                except Exception:
                    password = line
                session["auth_step"] = None
                expected = USERS.get(session["auth_user"])
                if expected == password:
                    session["authenticated"] = True
                    send("235 2.7.0 Authentication successful")
                else:
                    session["authenticated"] = False
                    session["auth_user"] = None
                    send("535 5.7.8 Authentication credentials invalid")

            # ── MAIL FROM ─────────────────────────────────────────────────
            elif cmd_word == "MAIL":
                # Nie wymagamy uwierzytelnienia (symulacja)
                # Wyciągamy adres z "MAIL FROM:<adres>"
                try:
                    addr_part = line.split(":", 1)[1].strip().strip("<>")
                except IndexError:
                    addr_part = "unknown"
                session["mail_from"] = addr_part
                session["rcpt_to"] = []
                session["data"] = ""
                send("250 2.1.0 Ok")

            # ── RCPT TO ───────────────────────────────────────────────────
            elif cmd_word == "RCPT":
                try:
                    addr_part = line.split(":", 1)[1].strip().strip("<>")
                except IndexError:
                    addr_part = "unknown"
                session["rcpt_to"].append(addr_part)
                send("250 2.1.5 Ok")

            # ── DATA ──────────────────────────────────────────────────────
            elif cmd_word == "DATA":
                if not session["mail_from"]:
                    send("503 5.5.1 Error: need MAIL command")
                    continue
                if not session["rcpt_to"]:
                    send("503 5.5.1 Error: need RCPT command")
                    continue
                send("354 End data with <CR><LF>.<CR><LF>")
                data_lines = []
                while True:
                    data_line = recv_line()
                    if data_line == ".":
                        break
                    # "byte-stuffing" - linia zaczynająca się od '..' -> '.'
                    if data_line.startswith(".."):
                        data_line = data_line[1:]
                    data_lines.append(data_line)
                session["data"] = "\n".join(data_lines)
                mail_id = save_email(session)
                send(f"250 OK: queued as {os.path.basename(mail_id)}")
                print(f"[SERWER] Od: {session['mail_from']}")
                print(f"[SERWER] Do: {session['rcpt_to']}")

            # ── RSET ──────────────────────────────────────────────────────
            elif cmd_word == "RSET":
                session["mail_from"] = None
                session["rcpt_to"] = []
                session["data"] = ""
                send("250 2.0.0 Ok")

            # ── NOOP ──────────────────────────────────────────────────────
            elif cmd_word == "NOOP":
                send("250 2.0.0 Ok")

            # ── VRFY ──────────────────────────────────────────────────────
            elif cmd_word == "VRFY":
                send("252 2.0.0 Cannot VRFY user")

            # ── QUIT ──────────────────────────────────────────────────────
            elif cmd_word == "QUIT":
                send("221 2.0.0 Bye")
                break

            # ── STARTTLS (symulacja - nie implementujemy TLS) ─────────────
            elif cmd_word == "STARTTLS":
                send("454 4.7.0 TLS not available")

            # ── Nieznana komenda ──────────────────────────────────────────
            else:
                send("500 5.5.2 Error: command not recognized")

    except (ConnectionResetError, BrokenPipeError):
        print(f"[SERWER] Klient {addr} rozłączył się niespodziewanie")
    finally:
        conn.close()
        print(f"[SERWER] Połączenie z {addr} zakończone")


def main():
    os.makedirs(SAVED_MAILS_DIR, exist_ok=True)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(10)
        print(f"[SERWER] Serwer SMTP nasłuchuje na {HOST}:{PORT}")
        print(f"[SERWER] Odebrane maile zapisywane w katalogu: {SAVED_MAILS_DIR}/")
        print(f"[SERWER] Ctrl+C aby zatrzymać\n")
        try:
            while True:
                conn, addr = srv.accept()
                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()
        except KeyboardInterrupt:
            print("\n[SERWER] Zatrzymano.")


if __name__ == "__main__":
    main()
