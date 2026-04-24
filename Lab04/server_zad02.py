import sys
import socket
from time import gmtime, strftime, perf_counter

HOST = '127.0.0.1'
PORT = 3000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


if __name__ == "__main__":
    try:
        sock.bind((HOST, PORT))
        sock.listen(1)
        print('Bind successful')
    except socket.error as msg:
        print('Bind failed. Error Code : ' + str(msg) + ' Message ' + str(msg))
        sys.exit()

    print("[%s] TCP ECHO Server is waiting for incoming connections ... " % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    try:
        conn, address = sock.accept()
        print(f"Connected with: {address}")
        while True:
            data = conn.recv(1024)
            print('[%s] Received %s bytes from client %s. Data: %s' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), len(data), address, data))

            if data:
                data = data.decode()
                if data.lower() == "exit":
                    sock.close()
                    break

                to_send = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                conn.sendall(to_send.encode())
                print('[%s] Sent %s bytes bytes back to client %s.' % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), to_send, address))
    finally:
        sock.close()
