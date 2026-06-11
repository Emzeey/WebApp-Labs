import socket
import os

HOST      = '127.0.0.1'
PORT      = 8080
RESOURCE  = '/image.jpg'
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'pobrane', 'image_zlozony.jpg')


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


def get_size() -> int:
    req = (
        f'GET {RESOURCE} HTTP/1.1\r\n'
        f'Host: {HOST}:{PORT}\r\n'
        f'User-Agent: PAN-Klient/1.0 (Python)\r\n'
        f'Accept: image/jpeg,image/*;q=0.9\r\n'
        f'Connection: close\r\n'
        f'\r\n'
    ).encode()

    print(f'[0] Pobieram metadane pliku ...')
    resp = send_request(req)
    headers_part, body_part = split_response(resp)
    hdrs = parse_headers(headers_part)

    status = headers_part.decode('utf-8', errors='replace').split('\r\n')[0]
    print(f'    Status: {status}')

    if 'content-length' in hdrs:
        size = int(hdrs['content-length'])
    else:
        size = len(body_part)

    print(f'    Content-Length: {size} B')
    return size


def get_part(num: int, start: int, end: int) -> bytes:
    req = (
        f'GET {RESOURCE} HTTP/1.1\r\n'
        f'Host: {HOST}:{PORT}\r\n'
        f'User-Agent: PAN-Klient/1.0 (Python)\r\n'
        f'Accept: image/jpeg,image/*;q=0.9\r\n'
        f'Range: bytes={start}-{end}\r\n'
        f'Connection: close\r\n'
        f'\r\n'
    ).encode()

    print(f'[{num}] Pobieranie części {num}: bytes={start}-{end} ({end-start+1} B) ...')
    resp = send_request(req)
    headers_part, body_part = split_response(resp)

    status = headers_part.decode('utf-8', errors='replace').split('\r\n')[0]
    hdrs   = parse_headers(headers_part)
    print(f'    Status: {status}')
    print(f'    Content-Range: {hdrs.get("content-range", "(brak)")}')

    if '206' not in status:
        raise RuntimeError(f'Oczekiwano 206 Partial Content, otrzymano: {status}')

    return body_part


def main():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    size = get_size()

    k = size // 3
    ranges = [
        (0,       k - 1),
        (k,       k * 2 - 1),
        (k * 2,   size - 1),
    ]
    print(f'\nPlan pobrania ({size} B → 3 części):')
    for i, (s, e) in enumerate(ranges, 1):
        print(f'  Część {i}: bytes={s}-{e}  ({e-s+1} B)')
    print()

    parts = [get_part(i, s, e) for i, (s, e) in enumerate(ranges, 1)]

    full_content = b''.join(parts)
    print(f'\nZłożony plik: {len(full_content)} B (oczekiwano {size} B)')
    assert len(full_content) == size, 'Rozmiar niezgodny!'

    with open(SAVE_PATH, 'wb') as f:
        f.write(full_content)
    print(f'✓ Zapisano: {SAVE_PATH}')


if __name__ == '__main__':
    main()