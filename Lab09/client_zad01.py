import socket
import os

HOST      = 'httpbin.org'
PORT      = 80
RESOURCE  = '/html'
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'pobrane', 'strona.html')

SAFARI_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) '
    'AppleWebKit/537.75.14 (KHTML, like Gecko) '
    'Version/7.0.3 Safari/537.75.14'
)


def build_request() -> bytes:
    return (
        f'GET {RESOURCE} HTTP/1.1\r\n'
        f'Host: {HOST}\r\n'
        f'User-Agent: {SAFARI_UA}\r\n'
        f'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n'
        f'Accept-Language: pl-PL,pl;q=0.9,en;q=0.8\r\n'
        f'Accept-Encoding: identity\r\n'
        f'Connection: close\r\n'
        f'\r\n'
    ).encode()


def main():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    request = build_request()
    print('── Wysyłane żądanie ──────────────────────────────')
    print(request.decode())

    print(f'Łączę się z {HOST}:{PORT} ...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.sendall(request)

    response = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    sock.close()

    idx     = response.find(b'\r\n\r\n')
    headers = response[:idx].decode('utf-8', errors='replace')
    body    = response[idx + 4:]

    print('── Nagłówki odpowiedzi ───────────────────────────')
    print(headers)
    print(f'\nRozmiar ciała: {len(body)} B')

    with open(SAVE_PATH, 'wb') as f:
        f.write(body)
    print(f'✓ Zapisano: {SAVE_PATH}')


if __name__ == '__main__':
    main()