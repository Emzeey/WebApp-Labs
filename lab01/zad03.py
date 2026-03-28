import ipaddress
import sys


def zad03() -> bool:
    try:
        ipaddress.ip_address(sys.argv[1])
        return True
    except ValueError:
        return False


print(zad03())
