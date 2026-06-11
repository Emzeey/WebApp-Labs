import socket
import os

HOST      = 'httpbin.org'
PORT      = 80
RESOURCE  = '/image/png'
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'pobrane', 'obrazek.png')


def build_request() -> bytes:
    return (
        f'GET {RESOURCE} HTTP/1.1\r\n'
        f'Host: {HOST}\r\n'
        f'User-Agent: PAN-Klient/1.0 (Python)\r\n'
        f'Accept: image/png,image/jpeg,image/*;q=0.9,*/*;q=0.5\r\n'
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
        chunk = sock.recv(8192)
        if not chunk:
            break
        response += chunk
    sock.close()

    idx     = response.find(b'\r\n\r\n')
    headers = response[:idx].decode('utf-8', errors='replace')
    body    = response[idx + 4:]

    print('── Nagłówki odpowiedzi ───────────────────────────')
    print(headers)
    print(f'Rozmiar ciała: {len(body)} B')

    if body[:4] == b'\x89PNG':
        print('✓ Sygnatura PNG poprawna')
    else:
        print(f'[?] Pierwsze bajty: {body[:8].hex()}')

    with open(SAVE_PATH, 'wb') as f:
        f.write(body)
    print(f'✓ Zapisano: {SAVE_PATH}')


if __name__ == '__main__':
    main()