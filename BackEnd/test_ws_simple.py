"""Quick WebSocket test - Run this while backend is running"""
import asyncio
import websockets
import json

async def test():
    print("Connecting to ws://localhost:8000/ws/analytics...")
    try:
        async with websockets.connect('ws://localhost:8000/ws/analytics') as ws:
            print("✅ Connected!")
            print("\nWaiting for first message...")
            
            msg = await ws.recv()
            data = json.loads(msg)
            
            print("\n📊 Received analytics data:")
            print(f"  Timestamp: {data.get('timestamp')}")
            print(f"  Prices: {data.get('prices')}")
            print(f"  Spread: {data.get('spread')}")
            print(f"  Z-Score: {data.get('z_score')}")
            print(f"  Correlation: {data.get('correlation')}")
            print("\n✅ WebSocket is working!")
            
    except ConnectionRefusedError:
        print("❌ Cannot connect - is backend running?")
        print("   Start it with: python run.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
