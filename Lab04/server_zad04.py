import sys
import socket
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 3000

def calculate(expression: str) -> str:
    try:
        parts = expression.split()

        if len(parts) != 3:
            return "Error: expected format: <number> <operator> <number>"

        a = float(parts[0])
        operator = parts[1]
        b = float(parts[2])

        if operator == '+':
            result = a + b
        elif operator == '-':
            result = a - b
        elif operator == '*':
            result = a * b
        elif operator == '/':
            if b == 0:
                return "Error: division by zero"
            result = a / b
        else:
            return f"Error: unknown operator '{operator}'. Use: + - * /"

        if result == int(result):
            return str(int(result))
        return str(result)

    except ValueError:
        return "Error: invalid number format"


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((HOST, PORT))
        print('Bind successful')
    except socket.error as msg:
        print('Bind failed. Error: ' + str(msg))
        sys.exit()

    print("[%s] UDP Calculator Server is waiting for incoming data..." % strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    print("Expected format: <number> <operator> <number>  e.g. '10 + 5' or '3.14 * 2'")

    try:
        while True:
            data, address = sock.recvfrom(1024)

            if not data:
                continue

            expression = data.decode().strip()
            print('[%s] Received from client %s: "%s"' % (
                strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, expression))

            if expression.lower() == "exit":
                print(f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] Client {address} requested exit.")
                continue

            result = calculate(expression)
            sock.sendto(result.encode(), address)
            print('[%s] Sent result to client %s: "%s"' % (
                strftime("%Y-%m-%d %H:%M:%S", gmtime()), address, result))

    finally:
        sock.close()