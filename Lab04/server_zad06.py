import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 3001

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((HOST, PORT))
        print('Bind successful')
    except socket.error as msg:
        print('Bind failed. Error: ' + str(msg))
        sys.exit()

    print("[%s] UDP Hostname->IP Server is waiting..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    try:
        while True:
            data, address = sock.recvfrom(1024)
            if not data:
                continue

            hostname = data.decode().strip()
            print('[%s] Received hostname from %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, hostname))

            try:
                ip = socket.gethostbyname(hostname)  # zwraca adres IP jako string
                result = ip
            except socket.gaierror:
                result = f"Error: cannot resolve IP for hostname '{hostname}'"

            sock.sendto(result.encode(), address)
            print('[%s] Sent to %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, result))
    finally:
        sock.close()