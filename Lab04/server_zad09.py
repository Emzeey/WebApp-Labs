import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 2910

UDP_RAW = bytes.fromhex("ed740b5500 24effd"
                         "70726f6772616d6d696e6720696e20707974686f6e20697320 66756e".replace(" ", ""))

EXPECTED_SRC  = int.from_bytes(UDP_RAW[0:2], 'big')   
EXPECTED_DST  = int.from_bytes(UDP_RAW[2:4], 'big')   
EXPECTED_DATA = UDP_RAW[8:].decode()                   

def validate(msg: str) -> str:
    parts = msg.split(';')
    if len(parts) != 7:
        return "BAD SYNTAX"
    if parts[0] != 'zad14odp':
        return "BAD SYNTAX"
    if parts[1] != 'src' or parts[3] != 'dst' or parts[5] != 'data':
        return "BAD SYNTAX"
    try:
        src  = int(parts[2])
        dst  = int(parts[4])
        data = parts[6]
    except ValueError:
        return "BAD SYNTAX"

    if src == EXPECTED_SRC and dst == EXPECTED_DST and data == EXPECTED_DATA:
        return "TAK"
    return "NIE"

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((HOST, PORT))
        print(f'Bind successful on {HOST}:{PORT}')
        print(f'Expected: src={EXPECTED_SRC}, dst={EXPECTED_DST}, data="{EXPECTED_DATA}"')
    except socket.error as msg:
        print('Bind failed. Error: ' + str(msg))
        sys.exit()

    print("[%s] Zadanie 9 UDP Server waiting..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    try:
        while True:
            data, address = sock.recvfrom(1024)
            if not data:
                continue

            msg = data.decode().strip()
            print('[%s] Received from %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, msg))

            result = validate(msg)
            sock.sendto(result.encode(), address)
            print('[%s] Sent to %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, result))
    finally:
        sock.close()