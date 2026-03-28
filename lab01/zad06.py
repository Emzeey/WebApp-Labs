import socket
import sys


def zad06():
    ip_address = sys.argv[1]
    port = int(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((ip_address, port))
            print("Connected")
        except:
            print("Cannot connect")


zad06()
