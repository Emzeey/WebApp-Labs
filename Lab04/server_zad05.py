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

    print("[%s] UDP IP->Hostname Server is waiting..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    try:
        while True:
            data, address = sock.recvfrom(1024)
            if not data:
                continue

            ip = data.decode().strip()
            print('[%s] Received IP from %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, ip))

            try:
                hostname = socket.gethostbyaddr(ip)[0]  # zwraca (hostname, aliasy, adresy)
                result = hostname
            except socket.herror:
                result = f"Error: cannot resolve hostname for IP '{ip}'"

            sock.sendto(result.encode(), address)
            print('[%s] Sent to %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, result))
    finally:
        sock.close()