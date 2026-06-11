import asyncio
import websockets


async def send_short_message():
    uri = "ws://127.0.0.1:8080"
    message = "Cześć! To jest krótka wiadomość tekstowa (poniżej 125 bajtów)."

    print(f"Rozmiar wiadomości: {len(message.encode('utf-8'))} bajtów.")

    try:
        async with websockets.connect(uri) as websocket:
            print("Połączono. Wysyłanie wiadomości...")
            await websocket.send(message)

            response = await websocket.recv()
            print(f"Odpowiedź serwera: {response}")
    except Exception as e:
        print(f"Błąd: {e}")


if __name__ == "__main__":
    asyncio.run(send_short_message())