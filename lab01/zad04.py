import sys
import socket


def zad04():
    ip_address = sys.argv[1]
    try:
        hostname, aliases, addresses = socket.gethostbyaddr(ip_address)
        print(f"Hostname: {hostname}")
    except (socket.herror, socket.gaierror, ValueError):
        print(f"Hostname for ip {ip_address} not found")


zad04()
