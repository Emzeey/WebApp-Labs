import socket
import threading
import time

HOST = "127.0.0.1"
TCP_PORT = 2904
UDP_PORT = 2905
BUFFER_SIZE = 65535


def tcp_echo():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, TCP_PORT))
        s.listen(1)
        print(f"[TCP Server] Listening on {HOST}:{TCP_PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                    conn.sendall(data)


def udp_echo():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, UDP_PORT))
        print(f"[UDP Server] Listening on {HOST}:{UDP_PORT}")

        while True:
            data, addr = s.recvfrom(BUFFER_SIZE)
            s.sendto(data, addr)


def ex04():
    print("=== TCP/UDP Echo Server ===")

    t1 = threading.Thread(target=tcp_echo, daemon=True)
    t2 = threading.Thread(target=udp_echo, daemon=True)

    t1.start()
    t2.start()

    print("Both servers running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")


if __name__ == "__main__":
    ex04()
