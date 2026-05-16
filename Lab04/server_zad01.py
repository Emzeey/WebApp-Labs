import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 3000

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

    print("[%s] TCP Server is waiting for incoming connections..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    try:
        while True:
            conn, address = sock.accept()
            print(f"Connected with: {address}")

            try:
                while True:
                    data = conn.recv(1024)

                    if not data:
                        print(f"Client {address} disconnected.")
                        break

                    print('[%s] Received %s bytes from client %s. Data: %s' % (
                        strftime("%Y-%m-%d %H:%M:%S", gmtime()), len(data), address, data))

                    decoded = data.decode()
                    if decoded.lower() == "exit":
                        break

                    to_send = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                    conn.sendall(to_send.encode())
                    print('[%s] Sent "%s" back to client %s.' % (
                        strftime("%Y-%m-%d %H:%M:%S", gmtime()), to_send, address))

            finally:
                conn.close()
    finally:
        sock.close()