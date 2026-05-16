import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 3000

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((HOST, PORT))
        print('Bind successful')
    except socket.error as msg:
        print('Bind failed. Error: ' + str(msg))
        sys.exit()

    print("[%s] UDP Echo Server is waiting for incoming data..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    try:
        while True:
            data, address = sock.recvfrom(1024)

            if not data:
                continue

            print('[%s] Received %s bytes from client %s. Data: %s' % (
                strftime("%Y-%m-%d %H:%M:%S", gmtime()), len(data), address, data.decode()))

            if data.decode().lower() == "exit":
                print(f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] Client {address} requested exit.")
                continue

            sock.sendto(data, address)
            print('[%s] Echoed %s bytes back to client %s.' % (
                strftime("%Y-%m-%d %H:%M:%S", gmtime()), len(data), address))

    finally:
        sock.close()