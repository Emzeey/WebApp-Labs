import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 3000
MAX_LEN = 20

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((HOST, PORT))
        sock.listen(1)
        print('Bind successful')
    except socket.error as msg:
        print('Bind failed. Error: ' + str(msg))
        sys.exit()

    print("[%s] TCP Echo Server (max %d chars) is waiting..." % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), MAX_LEN))

    try:
        while True:
            conn, address = sock.accept()
            print(f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] Connected with: {address}")

            try:
                while True:
                    data = conn.recv(MAX_LEN)

                    if not data:
                        print(f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] Client {address} disconnected.")
                        break

                    decoded = data.decode().strip()

                    if len(decoded) > MAX_LEN:
                        decoded = decoded[:MAX_LEN]
                        print('[%s] WARNING: message too long, truncated to %d chars.' % (
                            strftime("%Y-%m-%d %H:%M:%S", gmtime()), MAX_LEN))

                    print('[%s] Received %d bytes from %s: "%s"' % (
                        strftime("%Y-%m-%d %H:%M:%S", gmtime()), len(data), address, decoded))

                    if decoded.lower() == "exit":
                        break

                    to_send = decoded[:MAX_LEN]
                    conn.sendall(to_send.encode())
                    print('[%s] Echoed "%s" back to %s.' % (
                        strftime("%Y-%m-%d %H:%M:%S", gmtime()), to_send, address))

            finally:
                conn.close()
    finally:
        sock.close()