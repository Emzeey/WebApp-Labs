import socket
import random

HOST = "127.0.0.1"
PORT = 2902
RANGE_MIN = 1
RANGE_MAX = 100


def handle_client(conn, addr, secret):
    print(f"[SERVER] Connection from {addr}")
    print(f"[SERVER] Secret number: {secret}")

    greeting = f"Welcome! Guess a number between {RANGE_MIN} and {RANGE_MAX}.\n"
    conn.sendall(greeting.encode("utf-8"))

    buffer = ""
    with conn:
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                print("[SERVER] Client disconnected.")
                return

            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                message = line.strip()
                if not message:
                    continue

                print(f"[SERVER] Received: '{message}'")

                try:
                    number = int(message)
                except ValueError:
                    conn.sendall("ERROR: Value is not an integer.\n".encode("utf-8"))
                    continue

                if number < secret:
                    response = f"Too low! The number is greater than {number}.\n"
                elif number > secret:
                    response = f"Too high! The number is less than {number}.\n"
                else:
                    response = f"Correct! The secret number was {secret}. Game over.\n"
                    conn.sendall(response.encode("utf-8"))
                    print("[SERVER] Number guessed. Shutting down.")
                    return

                conn.sendall(response.encode("utf-8"))


def ex02():
    secret = random.randint(RANGE_MIN, RANGE_MAX)

    print("=== TCP Server - Number Guessing Game ===")
    print(f"Address : {HOST}:{PORT}")
    print(f"Range   : {RANGE_MIN}–{RANGE_MAX}")
    print("Waiting for a client...\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        conn, addr = server.accept()
        handle_client(conn, addr, secret)

    print("[SERVER] Server shut down.")


if __name__ == "__main__":
    ex02()
