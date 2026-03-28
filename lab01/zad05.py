import socket
import sys


def zad05():
    hostname = sys.argv[1]
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"Ip address: {ip_address}")
    except socket.gaierror:
        print(f"Ip address for hostname {hostname} not found")


zad05()
