"""
Test WebSocket /ws/analytics endpoint
Connects to backend and displays real-time analytics stream
"""
import asyncio
import websockets
import json
from datetime import datetime


async def test_analytics_websocket():
    """Connect to /ws/analytics and display stream."""
    uri = "ws://localhost:8000/ws/analytics"
    
    print("\n" + "="*70)
    print("  📡 WebSocket Analytics Stream Test")
    print("="*70)
    print(f"  Connecting to: {uri}")
    print("  Press Ctrl+C to stop")
    print("="*70 + "\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend!\n")
            print("Waiting for analytics data...\n")
            
            message_count = 0
            
            async for message in websocket:
                message_count += 1
                
                try:
                    data = json.loads(message)
                    
                    print("="*70)
                    print(f"  📊 Analytics Update #{message_count}")
                    print(f"  Received at: {datetime.now().strftime('%H:%M:%S')}")
                    print("="*70)
                    print(json.dumps(data, indent=2))
                    print("="*70 + "\n")
                    
                    # Validate payload structure
                    required_fields = ["timestamp", "prices", "spread", "z_score", "correlation"]
                    missing = [f for f in required_fields if f not in data]
                    
                    if missing:
                        print(f"⚠️  Missing fields: {missing}\n")
                    else:
                        print("✅ Payload structure matches specification!\n")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}\n")
                except Exception as e:
                    print(f"❌ Error processing message: {e}\n")
                
    except websockets.exceptions.ConnectionClosed:
        print("\n❌ Connection closed by server")
    except ConnectionRefusedError:
        print("\n❌ Connection refused. Is the backend running?")
        print("   Start it with: python backend/run.py")
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_analytics_websocket())
