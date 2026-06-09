import socket
import re
from datetime import datetime


class IMAPServer:
    def __init__(self, host='127.0.0.1', port=9143):
        self.host = host
        self.port = port
        self.server_socket = None
        self.mailboxes = {
            'INBOX': [
                ['Test email 1', 'This is a test email 1', False, False],
                ['Test email 2', 'This is a test email 2', False, False],
                ['Test email 3', 'This is a test email 3', True,  False],
            ],
            'SENT': [
                ['Sent email 1', 'This is a sent email', True, False],
            ],
            'DRAFTS': []
        }
        self.current_mailbox = None
        self.authenticated = False
        self.tag_counter = 0

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"Serwer IMAP nasłuchuje na {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Klient połączył się: {client_address}")
                self.handle_client(client_socket)
                client_socket.close()
        except KeyboardInterrupt:
            print("\nSerwer zatrzymany")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket):
        response = "* OK [CAPABILITY IMAP4rev1] Serwer IMAP\r\n"
        client_socket.send(response.encode())

        try:
            while True:
                request = client_socket.recv(4096).decode().strip()
                if not request:
                    break

                print(f"Otrzymano: {request}")

                parts = request.split()
                if not parts:
                    continue

                tag = parts[0]
                command = parts[1].upper() if len(parts) > 1 else ""
                args = parts[2:] if len(parts) > 2 else []

                if command == "CAPABILITY":
                    response = f"* CAPABILITY IMAP4rev1\r\n{tag} OK CAPABILITY completed\r\n"
                    client_socket.send(response.encode())

                elif command == "LOGIN":
                    if len(args) >= 2:
                        username = args[0].strip('"')
                        password = args[1].strip('"')
                        self.authenticated = True
                        response = f"{tag} OK LOGIN completed\r\n"
                        client_socket.send(response.encode())
                    else:
                        response = f"{tag} BAD Invalid LOGIN command\r\n"
                        client_socket.send(response.encode())

                elif command == "LIST":
                    if self.authenticated:
                        response = ""
                        for mailbox in self.mailboxes.keys():
                            response += f"* LIST (\\HasNoChildren) \"/\" \"{mailbox}\"\r\n"
                        response += f"{tag} OK LIST completed\r\n"
                        client_socket.send(response.encode())
                    else:
                        response = f"{tag} NO Not authenticated\r\n"
                        client_socket.send(response.encode())

                elif command == "SELECT":
                    if self.authenticated:
                        if len(args) > 0:
                            mailbox_name = args[0].strip('"')
                            if mailbox_name in self.mailboxes:
                                self.current_mailbox = mailbox_name
                                num_messages = len(self.mailboxes[mailbox_name])
                                response = f"* {num_messages} EXISTS\r\n"
                                response += f"* 0 RECENT\r\n"
                                response += f"* FLAGS (\\Seen \\Answered \\Flagged \\Deleted \\Draft)\r\n"
                                response += f"{tag} OK [READ-WRITE] SELECT completed\r\n"
                                client_socket.send(response.encode())
                            else:
                                response = f"{tag} NO Mailbox does not exist\r\n"
                                client_socket.send(response.encode())
                        else:
                            response = f"{tag} BAD Invalid SELECT command\r\n"
                            client_socket.send(response.encode())
                    else:
                        response = f"{tag} NO Not authenticated\r\n"
                        client_socket.send(response.encode())

                elif command == "FETCH":
                    if self.authenticated and self.current_mailbox:
                        if len(args) >= 2:
                            msg_num = int(args[0]) - 1
                            if 0 <= msg_num < len(self.mailboxes[self.current_mailbox]):
                                subject, body, seen, deleted = self.mailboxes[self.current_mailbox][msg_num]
                                email_content = f"From: sender@example.com\r\nTo: test@example.com\r\nSubject: {subject}\r\n\r\n{body}"
                                # FIX: no \r\n before closing ) — imaplib counts bytes exactly
                                response = f"* {msg_num + 1} FETCH (RFC822 {{{len(email_content)}}}\r\n{email_content})\r\n"
                                response += f"{tag} OK FETCH completed\r\n"
                                client_socket.send(response.encode())
                            else:
                                response = f"{tag} NO Message not found\r\n"
                                client_socket.send(response.encode())
                        else:
                            response = f"{tag} BAD Invalid FETCH command\r\n"
                            client_socket.send(response.encode())
                    else:
                        response = f"{tag} NO Not authenticated or mailbox not selected\r\n"
                        client_socket.send(response.encode())

                elif command == "STORE":
                    if self.authenticated and self.current_mailbox:
                        if len(args) >= 3:
                            msg_num = int(args[0]) - 1
                            flag_action = args[1]
                            flags = " ".join(args[2:])
                            if 0 <= msg_num < len(self.mailboxes[self.current_mailbox]):
                                subject, body, seen, deleted = self.mailboxes[self.current_mailbox][msg_num]
                                if "+FLAGS" in flag_action or "FLAGS" in flag_action:
                                    new_seen    = seen    or "\\Seen"    in flags
                                    new_deleted = deleted or "\\Deleted" in flags
                                    self.mailboxes[self.current_mailbox][msg_num] = [subject, body, new_seen, new_deleted]
                                response = f"* {msg_num + 1} FETCH (FLAGS (\\Seen))\r\n"
                                response += f"{tag} OK STORE completed\r\n"
                                client_socket.send(response.encode())
                            else:
                                response = f"{tag} NO Message not found\r\n"
                                client_socket.send(response.encode())
                        else:
                            response = f"{tag} BAD Invalid STORE command\r\n"
                            client_socket.send(response.encode())
                    else:
                        response = f"{tag} NO Not authenticated or mailbox not selected\r\n"
                        client_socket.send(response.encode())

                elif command == "SEARCH":
                    if self.authenticated and self.current_mailbox:
                        msg_ids = [str(i + 1) for i in range(len(self.mailboxes[self.current_mailbox]))]
                        response = f"* SEARCH {' '.join(msg_ids)}\r\n"
                        response += f"{tag} OK SEARCH completed\r\n"
                        client_socket.send(response.encode())
                    else:
                        response = f"{tag} NO Not authenticated or mailbox not selected\r\n"
                        client_socket.send(response.encode())

                elif command == "CLOSE":
                    # RFC 3501: permanently remove \Deleted messages, then deselect mailbox
                    if self.authenticated and self.current_mailbox:
                        self.mailboxes[self.current_mailbox] = [
                            msg for msg in self.mailboxes[self.current_mailbox] if not msg[3]
                        ]
                        self.current_mailbox = None
                        response = f"{tag} OK CLOSE completed\r\n"
                        client_socket.send(response.encode())
                    else:
                        response = f"{tag} NO Not authenticated or no mailbox selected\r\n"
                        client_socket.send(response.encode())

                elif command == "EXPUNGE":
                    # RFC 3501: permanently remove all \Deleted messages and report their sequence numbers
                    if self.authenticated and self.current_mailbox:
                        messages = self.mailboxes[self.current_mailbox]
                        new_messages = []
                        expunged = []

                        for i, msg in enumerate(messages):
                            subject, body, seen, deleted = msg
                            if deleted:
                                expunged.append(i + 1)
                            else:
                                new_messages.append(msg)

                        self.mailboxes[self.current_mailbox] = new_messages

                        response = ""
                        for msg_num in reversed(expunged):  # RFC 3501: highest sequence number first
                            response += f"* {msg_num} EXPUNGE\r\n"
                        response += f"{tag} OK EXPUNGE completed\r\n"
                        client_socket.send(response.encode())
                    else:
                        response = f"{tag} NO Not authenticated or mailbox not selected\r\n"
                        client_socket.send(response.encode())

                elif command == "LOGOUT":
                    response = f"* BYE Goodbye\r\n{tag} OK LOGOUT completed\r\n"
                    client_socket.send(response.encode())
                    break

                elif command in ["NOOP", "CHECK"]:
                    response = f"{tag} OK {command} completed\r\n"
                    client_socket.send(response.encode())

                else:
                    response = f"{tag} BAD Command '{command}' not implemented\r\n"
                    client_socket.send(response.encode())

        except Exception as e:
            print(f"Błąd: {e}")
        finally:
            print("Klient rozłączony")


if __name__ == "__main__":
    server = IMAPServer(host='127.0.0.1', port=9143)
    server.start()