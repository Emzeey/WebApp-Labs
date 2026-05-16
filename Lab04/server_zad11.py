import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 2911

IP_RAW = bytes.fromhex(
    "45000 04ef7fa40003806 9d33d4b6181bc0a80002"
    "0b54b9a6fbf93c57c10a06c1801800e3ce9c00000101080a03a6eb01000bf8e5"
    "6e6574776f726b2070726f6772616d6d696e6720697320 66756e".replace(" ", "")
)

ip_version  = IP_RAW[0] >> 4                                     
ip_ihl      = (IP_RAW[0] & 0x0F) * 4                            
ip_proto    = IP_RAW[9]                                          
src_ip      = '.'.join(str(b) for b in IP_RAW[12:16])           
dst_ip      = '.'.join(str(b) for b in IP_RAW[16:20])

tcp_start   = ip_ihl
src_port    = int.from_bytes(IP_RAW[tcp_start:tcp_start+2], 'big')      
dst_port    = int.from_bytes(IP_RAW[tcp_start+2:tcp_start+4], 'big')    
tcp_offset  = (IP_RAW[tcp_start+12] >> 4) * 4                           
data_start  = tcp_start + tcp_offset
EXPECTED_DATA = IP_RAW[data_start:].decode()                             

def validate_a(msg: str) -> str:
    parts = msg.split(';')
    if len(parts) != 9:
        return "BAD SYNTAX"
    if parts[0] != 'zad15odpA':
        return "BAD SYNTAX"
    if parts[1] != 'ver' or parts[3] != 'srcip' or parts[5] != 'dstip' or parts[7] != 'type':
        return "BAD SYNTAX"
    try:
        ver   = int(parts[2])
        srcip = parts[4]
        dstip = parts[6]
        proto = int(parts[8])
    except ValueError:
        return "BAD SYNTAX"

    if ver == ip_version and srcip == src_ip and dstip == dst_ip and proto == ip_proto:
        return "TAK"
    return "NIE"

def validate_b(msg: str) -> str:
    parts = msg.split(';')
    if len(parts) != 7:
        return "BAD SYNTAX"
    if parts[0] != 'zad15odpB':
        return "BAD SYNTAX"
    if parts[1] != 'srcport' or parts[3] != 'dstport' or parts[5] != 'data':
        return "BAD SYNTAX"
    try:
        src  = int(parts[2])
        dst  = int(parts[4])
        data = parts[6]
    except ValueError:
        return "BAD SYNTAX"

    if src == src_port and dst == dst_port and data == EXPECTED_DATA:
        return "TAK"
    return "NIE"

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((HOST, PORT))
        print(f'Bind successful on {HOST}:{PORT}')
        print(f'Expected A: ver={ip_version}, srcip={src_ip}, dstip={dst_ip}, proto={ip_proto}')
        print(f'Expected B: srcport={src_port}, dstport={dst_port}, data="{EXPECTED_DATA}"')
    except socket.error as msg:
        print('Bind failed. Error: ' + str(msg))
        sys.exit()

    print("[%s] Zadanie 11 UDP Server waiting..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    try:
        while True:
            data, address = sock.recvfrom(1024)
            if not data:
                continue

            msg = data.decode().strip()
            print('[%s] Received from %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, msg))

            if msg.startswith('zad15odpA'):
                result = validate_a(msg)
            elif msg.startswith('zad15odpB'):
                result = validate_b(msg)
            else:
                result = "BAD SYNTAX"

            sock.sendto(result.encode(), address)
            print('[%s] Sent to %s: "%s"' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, result))
    finally:
        sock.close()