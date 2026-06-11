import socket
import os
from email.utils import formatdate

HOST      = '127.0.0.1'
PORT      = 8080
RESOURCE  = '/image.jpg'
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'pobrane', 'image_warunkowy.jpg')
META_PATH = SAVE_PATH + '.meta'   


def send_request(request: bytes) -> bytes:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.sendall(request)
    buf = b''
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        buf += chunk
    sock.close()
    return buf


def split_response(data: bytes):
    idx = data.find(b'\r\n\r\n')
    return data[:idx], data[idx + 4:]


def parse_headers(raw: bytes) -> dict:
    d = {}
    for line in raw.decode('utf-8', errors='replace').split('\r\n')[1:]:
        if ': ' in line:
            k, v = line.split(': ', 1)
            d[k.lower()] = v
    return d


def build_request(if_modified_since: str = None) -> bytes:
    lines = [
        f'GET {RESOURCE} HTTP/1.1',
        f'Host: {HOST}:{PORT}',
        f'User-Agent: PAN-Klient/1.0 (Python)',
        f'Accept: image/jpeg,image/*;q=0.9,*/*;q=0.5',
        f'Accept-Encoding: identity',
    ]
    if if_modified_since:
        lines.append(f'If-Modified-Since: {if_modified_since}')
    lines.append('Connection: close')
    lines += ['', '']
    return '\r\n'.join(lines).encode()


def load_date() -> str:
    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            return f.read().strip()
    return None


def save_date(date_str: str):
    with open(META_PATH, 'w') as f:
        f.write(date_str)


def main():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    previous_date = load_date()

    if previous_date:
        print(f'Ostatnie pobranie: {previous_date}')
        print('Wysyłam żądanie warunkowe (If-Modified-Since) ...\n')
    else:
        print('Pierwsze pobranie — brak danych meta.')
        print('Wysyłam zwykłe GET ...\n')

    request = build_request(if_modified_since=previous_date)

    print('── Wysyłane żądanie ──────────────────────────────')
    print(request.decode('utf-8', errors='replace'))

    response = send_request(request)
    headers_bytes, body = split_response(response)
    headers_str = headers_bytes.decode('utf-8', errors='replace')
    status      = headers_str.split('\r\n')[0]
    hdrs        = parse_headers(headers_bytes)

    print('── Nagłówki odpowiedzi ───────────────────────────')
    print(headers_str)

    if '304' in status:
        print('✓ 304 Not Modified — plik nie zmienił się od ostatniego pobrania.')
        print('  Używam wersji z dysku. Plik NIE został pobrany ponownie.')

    elif '200' in status:
        print(f'✓ 200 OK — nowa wersja pliku ({len(body)} B).')
        with open(SAVE_PATH, 'wb') as f:
            f.write(body)
        print(f'  Zapisano: {SAVE_PATH}')

        last_mod = hdrs.get('last-modified', formatdate(usegmt=True))
        save_date(last_mod)
        print(f'  Zapamiętano Last-Modified: {last_mod}')

    else:
        print(f'[!] Nieoczekiwany status: {status}')

    print('\n(Uruchom ponownie, aby zobaczyć 304 Not Modified)')


if __name__ == '__main__':
    main()