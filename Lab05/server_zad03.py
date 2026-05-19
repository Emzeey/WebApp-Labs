import socket
import threading
import time
from collections import defaultdict

HOST = "127.0.0.1"
KNOCK_SEQUENCE = [1666, 7666, 3666]
TCP_PORT = 2903
SUCCESS_MESSAGE = "Congratulations! You found the hidden service!\n"
UDP_BUFFER = 1024
RESET_AFTER_SECONDS = 30

client_progress = defaultdict(int)
client_last_knock = defaultdict(float)
state_lock = threading.Lock()
tcp_unlocked = threading.Event()


def udp_worker(port, index):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port))
        print(f"[UDP] Listening on port {port} (position {index + 1} in sequence)")

        while True:
            try:
                data, client_addr = s.recvfrom(UDP_BUFFER)
            except OSError:
                break

            client_ip = client_addr[0]
            message = data.decode("utf-8", errors="replace").strip()

            if message != "PING":
                continue

            now = time.time()

            with state_lock:
                if now - client_last_knock[client_ip] > RESET_AFTER_SECONDS:
                    client_progress[client_ip] = 0

                client_last_knock[client_ip] = now
                expected = client_progress[client_ip]

                if index == expected:
                    client_progress[client_ip] += 1
                    progress = client_progress[client_ip]
                    print(f"[UDP] {client_ip} -> port {port} PONG ({progress}/{len(KNOCK_SEQUENCE)})")
                    s.sendto(b"PONG", client_addr)

                    if progress == len(KNOCK_SEQUENCE):
                        print(f"[UDP] {client_ip} completed the sequence! Unlocking TCP.")
                        tcp_unlocked.set()
                        client_progress[client_ip] = 0
                else:
                    print(f"[UDP] {client_ip} -> port {port} wrong order (expected pos {expected}), resetting")
                    client_progress[client_ip] = 0


def tcp_worker():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, TCP_PORT))
        s.listen(5)
        s.settimeout(1.0)

        print(f"[TCP] Hidden service waiting on port {TCP_PORT} (locked until knock sequence)")

        while True:
            tcp_unlocked.wait()
            print(f"[TCP] Port {TCP_PORT} unlocked - waiting for connection...")

            try:
                conn, addr = s.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with conn:
                print(f"[TCP] Connected: {addr}")
                conn.sendall(SUCCESS_MESSAGE.encode("utf-8"))

            tcp_unlocked.clear()
            print(f"[TCP] Port {TCP_PORT} locked again.\n")


def ex03():
    print("=== Port-Knocking Server ===")
    print(f"Host           : {HOST}")
    print(f"Knock sequence : {KNOCK_SEQUENCE}")
    print(f"Hidden TCP port: {TCP_PORT}")
    print("=" * 40 + "\n")

    threads = []

    for i, port in enumerate(KNOCK_SEQUENCE):
        t = threading.Thread(target=udp_worker, args=(port, i), daemon=True, name=f"UDP-{port}")
        t.start()
        threads.append(t)

    t_tcp = threading.Thread(target=tcp_worker, daemon=True, name="TCP-hidden")
    t_tcp.start()
    threads.append(t_tcp)

    print("Server running. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SERVER] Stopping...")


if __name__ == "__main__":
    ex03()
