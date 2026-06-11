import asyncio
import websockets


async def connect_client():
    uri = "ws://127.0.0.1:8080"

    print(f"Próba nawiązania połączenia (handshake) z {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Sukces! Handshake zakończony pomyślnie. Połączenie nawiązane.")
    except Exception as e:
        print(f"Błąd podczas łączenia: {e}")


if __name__ == "__main__":
    asyncio.run(connect_client())