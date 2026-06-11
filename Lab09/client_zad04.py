import socket
import os
from urllib.parse import quote_plus

HOST     = 'httpbin.org'
PORT     = 80
RESOURCE = '/post'


def url_encode(data: dict) -> str:
    return '&'.join(f'{quote_plus(k)}={quote_plus(v)}' for k, v in data.items())


def build_request(body_str: str) -> bytes:
    body_bytes = body_str.encode('utf-8')
    headers = (
        f'POST {RESOURCE} HTTP/1.1\r\n'
        f'Host: {HOST}\r\n'
        f'User-Agent: PAN-Klient/1.0 (Python)\r\n'
        f'Content-Type: application/x-www-form-urlencoded\r\n'
        f'Content-Length: {len(body_bytes)}\r\n'
        f'Accept: application/json,*/*;q=0.8\r\n'
        f'Connection: close\r\n'
        f'\r\n'
    ).encode()
    return headers + body_bytes


def main():
    print('=== Zadanie 4 – Wysyłanie formularza POST ===\n')
    print('Wypełnij pola formularza (Enter = wartość domyślna):\n')

    first_name = input('Imię       [Jan]:           ').strip() or 'Jan'
    last_name  = input('Nazwisko   [Kowalski]:       ').strip() or 'Kowalski'
    email      = input('E-mail     [jan@example.com]:').strip() or 'jan@example.com'
    message    = input('Wiadomość  [Witaj!]:         ').strip() or 'Witaj!'

    data = {
        'imie':      first_name,
        'nazwisko':  last_name,
        'email':     email,
        'wiadomosc': message,
    }

    body = url_encode(data)
    request = build_request(body)

    print('\n── Wysyłane żądanie ──────────────────────────────')
    print(request.decode('utf-8', errors='replace'))
    print('─' * 50)

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

    print('\n── Odpowiedź serwera ─────────────────────────────')
    print(response.decode('utf-8', errors='replace'))


if __name__ == '__main__':
    main()