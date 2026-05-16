import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 2909

TCP_RAW = bytes.fromhex(
    "0b54898b1f9a18ecbbb164f2801800e3677100000101080a02c1a4ee001a4cee"
    "68656c6c6f203a29"
)

EXPECTED_SRC  = int.from_bytes(TCP_RAW[0:2], 'big')    
EXPECTED_DST  = int.from_bytes(TCP_RAW[2:4], 'big')    
data_offset   = (TCP_RAW[12] >> 4) * 4                 
EXPECTED_DATA = TCP_RAW[data_offset:].decode()          

def validate(msg: str) -> str:
    parts = msg.split(';')
    if len(parts) != 7:
        return "BAD SYNTAX"
    if parts[0] != 'zad13odp':
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

    print("[%s] Zadanie 10 UDP Server waiting..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

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