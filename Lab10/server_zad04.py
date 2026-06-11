import asyncio
import websockets

async def echo_handler(websocket):
    print(f"Nowe połączenie od: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Otrzymano od klienta: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosedOK:
        print("Klient rozłączył się prawidłowo.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Połączenie przerwane z błędem: {e}")
    finally:
        print("Zakończono obsługę klienta. Serwer czeka na kolejnego...")

async def main():
    async with websockets.serve(echo_handler, "127.0.0.1", 8080):
        print("Serwer WebSocket działa na ws://127.0.0.1:8080")
        await asyncio.Future()  # Działa bezterminowo

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")