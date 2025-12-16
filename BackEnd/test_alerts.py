"""
Test alert system - connects to WebSocket and displays alerts
"""
import asyncio
import websockets
import json
from datetime import datetime


async def test_alerts_websocket():
    """Connect to /ws/alerts and display alert stream."""
    uri = "ws://localhost:8000/ws/alerts"
    
    print("\n" + "="*70)
    print("  🚨 Alert System Test")
    print("="*70)
    print(f"  Connecting to: {uri}")
    print("  Press Ctrl+C to stop")
    print("  Waiting for alerts (z-score > 2.0, low correlation, etc.)")
    print("="*70 + "\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to alert stream!\n")
            
            alert_count = 0
            
            async for message in websocket:
                alert_count += 1
                
                try:
                    data = json.loads(message)
                    
                    print("="*70)
                    print(f"  🚨 ALERT #{alert_count}")
                    print(f"  Received at: {datetime.now().strftime('%H:%M:%S')}")
                    print("="*70)
                    
                    # Display alert data
                    alert_data = data.get('data', {})
                    
                    print(f"  Type:      {alert_data.get('type', 'N/A')}")
                    print(f"  Title:     {alert_data.get('title', 'N/A')}")
                    print(f"  Message:   {alert_data.get('message', 'N/A')}")
                    
                    if alert_data.get('metric'):
                        print(f"\n  📊 Metrics:")
                        print(f"     Metric:    {alert_data.get('metric')}")
                        print(f"     Value:     {alert_data.get('value', 'N/A')}")
                        print(f"     Threshold: {alert_data.get('threshold', 'N/A')}")
                        print(f"     Direction: {alert_data.get('direction', 'N/A')}")
                    
                    print("="*70 + "\n")
                    
                    # Validate Step 7 format
                    if alert_data.get('type') == 'ALERT':
                        required = ['metric', 'value', 'threshold', 'direction']
                        missing = [f for f in required if f not in alert_data]
                        
                        if missing:
                            print(f"⚠️  Missing Step 7 fields: {missing}\n")
                        else:
                            print("✅ Alert matches Step 7 specification!\n")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}\n")
                except Exception as e:
                    print(f"❌ Error processing message: {e}\n")
                
    except websockets.exceptions.ConnectionClosed:
        print("\n❌ Connection closed by server")
    except ConnectionRefusedError:
        print("\n❌ Connection refused. Is the backend running?")
        print("   Start it with: python run.py")
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_alerts_websocket())
