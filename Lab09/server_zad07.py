import socket
import os
import mimetypes
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime, formatdate

HOST    = '127.0.0.1'
PORT    = 8080
WWW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'www')


def parse_request(raw: str):
    lines = raw.split('\r\n')
    parts = lines[0].split(' ')
    if len(parts) != 3:
        raise ValueError('Niepoprawna linia żądania')
    method, path, version = parts
    headers = {}
    for line in lines[1:]:
        if ': ' in line:
            k, v = line.split(': ', 1)
            headers[k.lower()] = v
    return method, path, version, headers


def resolve_path(url_path: str) -> str:
    if url_path in ('/', ''):
        url_path = '/index.html'
    url_path = url_path.split('?')[0]          
    safe = os.path.normpath(url_path.lstrip('/'))
    return os.path.join(WWW_DIR, safe)


def build_response(status: int, reason: str, extra_headers: dict, body: bytes) -> bytes:
    lines = [f'HTTP/1.1 {status} {reason}']
    lines.append(f'Date: {formatdate(usegmt=True)}')
    lines.append('Server: PAN-HTTP/1.0 (Python)')
    lines.append('Connection: close')
    for k, v in extra_headers.items():
        lines.append(f'{k}: {v}')
    lines.append('')   
    lines.append('')
    return '\r\n'.join(lines).encode() + body


def serve_file(file_path: str, req_headers: dict) -> bytes:
    stat        = os.stat(file_path)
    file_size   = stat.st_size
    mtime       = stat.st_mtime
    last_mod    = formatdate(mtime, usegmt=True)
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'

    if 'if-modified-since' in req_headers:
        try:
            ims     = parsedate_to_datetime(req_headers['if-modified-since'])
            file_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            if file_dt <= ims:
                return build_response(304, 'Not Modified', {
                    'Last-Modified': last_mod,
                }, b'')
        except Exception:
            pass  

    if 'range' in req_headers:
        try:
            spec = req_headers['range'].strip()
            assert spec.startswith('bytes=')
            start_s, end_s = spec[6:].split('-')
            start = int(start_s) if start_s else 0
            end   = int(end_s)   if end_s   else file_size - 1
            end   = min(end, file_size - 1)

            if start > end or start >= file_size:
                return build_response(416, 'Range Not Satisfiable', {
                    'Content-Range': f'bytes */{file_size}',
                }, b'')

            with open(file_path, 'rb') as f:
                f.seek(start)
                body = f.read(end - start + 1)

            return build_response(206, 'Partial Content', {
                'Content-Type':   content_type,
                'Content-Length': str(len(body)),
                'Content-Range':  f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges':  'bytes',
                'Last-Modified':  last_mod,
            }, body)
        except Exception:
            pass  

    with open(file_path, 'rb') as f:
        body = f.read()

    return build_response(200, 'OK', {
        'Content-Type':   content_type,
        'Content-Length': str(file_size),
        'Accept-Ranges':  'bytes',
        'Last-Modified':  last_mod,
    }, body)


def handle_connection(conn: socket.socket, addr: tuple):
    raw = b''
    try:
        while b'\r\n\r\n' not in raw:
            chunk = conn.recv(4096)
            if not chunk:
                break
            raw += chunk
    except Exception as e:
        print(f'  [!] Błąd odbioru od {addr}: {e}')
        conn.close()
        return

    if not raw:
        conn.close()
        return

    req_str    = raw.decode('utf-8', errors='replace')
    first_line = req_str.split('\r\n')[0]
    print(f'[{addr[0]}:{addr[1]}] {first_line}')

    try:
        method, path, version, req_headers = parse_request(req_str)
    except Exception as e:
        print(f'  → 400 Bad Request ({e})')
        conn.sendall(build_response(400, 'Bad Request', {'Content-Length': '0'}, b''))
        conn.close()
        return

    if method != 'GET':
        print(f'  → 405 Method Not Allowed')
        conn.sendall(build_response(405, 'Method Not Allowed',
                                    {'Allow': 'GET', 'Content-Length': '0'}, b''))
        conn.close()
        return

    file_path = resolve_path(path)

    if not os.path.isfile(file_path):
        err_path = os.path.join(WWW_DIR, '404.html')
        if os.path.isfile(err_path):
            with open(err_path, 'rb') as f:
                body = f.read()
        else:
            body = b'<h1>404 Not Found</h1>'
        print(f'  → 404 Not Found')
        conn.sendall(build_response(404, 'Not Found', {
            'Content-Type':   'text/html; charset=utf-8',
            'Content-Length': str(len(body)),
        }, body))
        conn.close()
        return

    response = serve_file(file_path, req_headers)
    conn.sendall(response)
    conn.close()


def main():
    os.makedirs(WWW_DIR, exist_ok=True)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(5)

    print('╔══════════════════════════════════════════════╗')
    print('║  Serwer HTTP  –  Zadanie 7  (PAN)            ║')
    print('╠══════════════════════════════════════════════╣')
    print(f'║  http://{HOST}:{PORT}/                      ║')
    print(f'║  Katalog: {WWW_DIR[-36:]:<36}║')
    print('╚══════════════════════════════════════════════╝')
    print('Ctrl+C aby zatrzymać.\n')

    while True:
        try:
            conn, addr = srv.accept()
            handle_connection(conn, addr)
        except KeyboardInterrupt:
            print('\nSerwer zatrzymany.')
            break
        except Exception as e:
            print(f'[!] Błąd: {e}')

    srv.close()


if __name__ == '__main__':
    main()