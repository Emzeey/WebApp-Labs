import socket
import threading
import base64

HOST = "127.0.0.1"
PORT = 110

MAILBOX_USER = "pasinf2017@infumcs.edu"
MAILBOX_PASS = "P4SInf2017"


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    return s


def recv_line(s):
    data = b""
    while not data.endswith(b"\r\n"):
        data += s.recv(1)
    return data.decode("ascii", errors="replace").strip()


def recv_multiline(s):
    lines = []
    while True:
        line = recv_line(s)
        if line == ".":
            break
        if line.startswith(".."):
            line = line[1:]
        lines.append(line)
    return lines


def send_cmd(s, cmd):
    s.sendall((cmd + "\r\n").encode("ascii"))


def login(s):
    recv_line(s)
    send_cmd(s, f"USER {MAILBOX_USER}")
    recv_line(s)
    send_cmd(s, f"PASS {MAILBOX_PASS}")
    resp = recv_line(s)
    if not resp.startswith("+OK"):
        raise RuntimeError(f"Login failed: {resp}")


def quit_session(s):
    send_cmd(s, "QUIT")
    recv_line(s)
    s.close()


def stat(s):
    send_cmd(s, "STAT")
    resp = recv_line(s)
    parts = resp.split()
    return int(parts[1]), int(parts[2])


def list_messages(s):
    send_cmd(s, "LIST")
    recv_line(s)
    lines = recv_multiline(s)
    result = []
    for line in lines:
        num, size = line.split()
        result.append((int(num), int(size)))
    return result


def retr(s, num):
    send_cmd(s, f"RETR {num}")
    recv_line(s)
    return recv_multiline(s)


def dele(s, num):
    send_cmd(s, f"DELE {num}")
    return recv_line(s)


def make_png():
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAoElEQVR4nA3J0RQAQAhF"
        "wTTSSCONNDrnUjyNNNLIZHd+x8xwI4w0ymhDxhhrnGHmuBNOOuW0I2ecdc5/Bx5EkEEF"
        "HSiYYIOL34knkWRSSSdKJtnk8nfhRRRZVNGFiim2uPrdeBNNNtV0o2aaba5/CxchUpRo"
        "ITFixen34EMMOdTQg4YZdrj5vfgSSy619KJlll1ufx9+xJFHHX3omGOPOx7JKonl1xxB"
        "AwAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(png_b64)


PNG_B64 = base64.encodebytes(make_png()).decode("ascii")


def build_message_with_attachment():
    boundary = "----=_Part_42_attachment"
    return (
        "From: charlie@example.com\r\n"
        "To: pasinf2017@infumcs.edu\r\n"
        "Subject: Image attached\r\n"
        "Date: Wed, 03 Jan 2024 12:00:00 +0000\r\n"
        "MIME-Version: 1.0\r\n"
        f"Content-Type: multipart/mixed; boundary=\"{boundary}\"\r\n"
        "\r\n"
        f"--{boundary}\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        "Please find the image attached.\r\n"
        "\r\n"
        f"--{boundary}\r\n"
        "Content-Type: image/png; name=\"attachment.png\"\r\n"
        "Content-Transfer-Encoding: base64\r\n"
        "Content-Disposition: attachment; filename=\"attachment.png\"\r\n"
        "\r\n"
        + PNG_B64
        + f"\r\n--{boundary}--\r\n"
    )


msg3_content = build_message_with_attachment()

MESSAGES = [
    {
        "id": 1,
        "size": 312,
        "content": (
            "From: alice@example.com\r\n"
            "To: pasinf2017@infumcs.edu\r\n"
            "Subject: Hello\r\n"
            "Date: Mon, 01 Jan 2024 10:00:00 +0000\r\n"
            "\r\n"
            "Hi there!\r\n"
            "This is a short test message.\r\n"
            "Best regards,\r\nAlice\r\n"
        ),
        "deleted": False,
    },
    {
        "id": 2,
        "size": 198,
        "content": (
            "From: bob@example.com\r\n"
            "To: pasinf2017@infumcs.edu\r\n"
            "Subject: Quick note\r\n"
            "Date: Tue, 02 Jan 2024 09:30:00 +0000\r\n"
            "\r\n"
            "Just a quick note.\r\n"
            "Bob\r\n"
        ),
        "deleted": False,
    },
    {
        "id": 3,
        "size": len(msg3_content.encode("ascii", errors="replace")),
        "content": msg3_content,
        "deleted": False,
    },
]


def send(conn, text):
    conn.sendall((text + "\r\n").encode("ascii", errors="replace"))


def recv_line(conn):
    data = b""
    while True:
        chunk = conn.recv(1)
        if not chunk:
            break
        data += chunk
        if data.endswith(b"\n"):
            break
    return data.decode("ascii", errors="replace").strip("\r\n \t\x00")


def handle_client(conn, addr):
    print(f"[SERVER] Connection from {addr}")
    messages = [dict(m) for m in MESSAGES]

    send(conn, "+OK POP3 server ready")

    state = "AUTH"
    authenticated_user = None

    try:
        while True:
            line = recv_line(conn)
            if not line:
                break

            print(f"[SERVER] <- {repr(line)}")
            parts = line.split(" ", 1)
            cmd = parts[0].upper()
            arg = parts[1].strip("\r\n \t\x00") if len(parts) > 1 else ""

            if state == "AUTH":
                if cmd == "USER":
                    if arg:
                        authenticated_user = arg
                        send(conn, f"+OK {arg} welcome")
                    else:
                        send(conn, "-ERR Missing username")

                elif cmd == "PASS":
                    if authenticated_user is None:
                        send(conn, "-ERR Send USER first")
                    elif arg == MAILBOX_PASS:
                        state = "TRANSACTION"
                        send(conn, "+OK Mailbox locked and ready")
                    else:
                        print(f"[SERVER] PASS mismatch: got={repr(arg)} expected={repr(MAILBOX_PASS)}")
                        send(conn, "-ERR Invalid password")
                        authenticated_user = None

                elif cmd == "QUIT":
                    send(conn, "+OK Bye")
                    break

                else:
                    send(conn, "-ERR Command not implemented in AUTH state")

            elif state == "TRANSACTION":
                if cmd == "STAT":
                    active = [m for m in messages if not m["deleted"]]
                    total = sum(m["size"] for m in active)
                    send(conn, f"+OK {len(active)} {total}")

                elif cmd == "LIST":
                    active = [m for m in messages if not m["deleted"]]
                    send(conn, f"+OK {len(active)} messages")
                    for m in active:
                        conn.sendall(f"{m['id']} {m['size']}\r\n".encode("ascii"))
                    conn.sendall(b".\r\n")

                elif cmd == "RETR":
                    try:
                        num = int(arg)
                        msg = next((m for m in messages if m["id"] == num and not m["deleted"]), None)
                        if msg is None:
                            send(conn, "-ERR No such message")
                        else:
                            send(conn, f"+OK {msg['size']} octets")
                            for line_text in msg["content"].splitlines():
                                if line_text == ".":
                                    line_text = ".."
                                conn.sendall((line_text + "\r\n").encode("ascii", errors="replace"))
                            conn.sendall(b".\r\n")
                    except ValueError:
                        send(conn, "-ERR Invalid message number")

                elif cmd == "DELE":
                    try:
                        num = int(arg)
                        msg = next((m for m in messages if m["id"] == num and not m["deleted"]), None)
                        if msg is None:
                            send(conn, "-ERR No such message")
                        else:
                            msg["deleted"] = True
                            send(conn, f"+OK Message {num} deleted")
                    except ValueError:
                        send(conn, "-ERR Invalid message number")

                elif cmd == "RSET":
                    for m in messages:
                        m["deleted"] = False
                    send(conn, "+OK Maildrop has been reset")

                elif cmd == "NOOP":
                    send(conn, "+OK")

                elif cmd == "QUIT":
                    send(conn, "+OK Bye")
                    break

                else:
                    send(conn, "-ERR Command not implemented")

            else:
                send(conn, "-ERR Unknown state")
                break

    except (ConnectionResetError, BrokenPipeError):
        print(f"[SERVER] Client {addr} disconnected unexpectedly")
    finally:
        conn.close()
        print(f"[SERVER] Connection with {addr} closed")


def ex12():
    print("=== POP3 Server (simulation) ===")
    print(f"Address  : {HOST}:{PORT}")
    print(f"User     : {MAILBOX_USER}")
    print(f"Password : {MAILBOX_PASS}")
    print(f"Messages : {len(MESSAGES)}")
    print("Waiting for connection...\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)

        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    ex12()