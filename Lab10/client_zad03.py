import asyncio
import websockets


async def send_long_message():
    uri = "ws://127.0.0.1:8080"

    message = "To jest bardzo długa wiadomość tekstowa. " * 100
    print(f"Rozmiar wiadomości: {len(message.encode('utf-8'))} bajtów.")

    try:
        async with websockets.connect(uri) as websocket:
            print("Połączono. Wysyłanie długiej wiadomości...")
            await websocket.send(message)

            response = await websocket.recv()
            print(f"Otrzymano odpowiedź o długości: {len(response)} znaków.")
            print(f"Początek odpowiedzi: {response[:50]}...")
    except Exception as e:
        print(f"Błąd: {e}")


if __name__ == "__main__":
    asyncio.run(send_long_message())