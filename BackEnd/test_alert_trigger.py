"""
Manually trigger alert to demonstrate Step 7 alert format
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.alerts import get_alert_manager
from app.websocket_manager import get_connection_manager
from app.schemas import SpreadDataPoint
from datetime import datetime
import json


async def trigger_and_display_alert():
    """Create a sample alert that exceeds z-score threshold."""
    
    alerts = get_alert_manager()
    ws_manager = get_connection_manager()
    
    print("\n" + "="*70)
    print("  🚨 Step 7: Alert System Demo")
    print("="*70)
    print("  Generating alert with z-score > 2.0...")
    print("="*70 + "\n")
    
    # Create spread data with high z-score
    spread_data = SpreadDataPoint(
        timestamp=int(datetime.utcnow().timestamp() * 1000),
        time=datetime.utcnow().strftime('%H:%M:%S'),
        spread=125.5,
        zScore=2.15,  # Above threshold!
        upperThreshold=2.0,
        lowerThreshold=-2.0
    )
    
    # Store original callback
    original_callbacks = alerts.alert_callbacks.copy()
    alerts.alert_callbacks.clear()
    
    # Add custom callback to capture alert
    captured_alert = None
    
    def capture_alert(alert):
        nonlocal captured_alert
        captured_alert = alert
    
    alerts.subscribe(capture_alert)
    
    # Trigger z-score alert
    await alerts.evaluate_zscore_alert(spread_data, threshold=2.0)
    
    # Display alert in Step 7 format
    if captured_alert:
        # Extract clean alert format
        alert_message = {
            "type": captured_alert.type,
            "metric": captured_alert.metric,
            "value": captured_alert.value,
            "threshold": captured_alert.threshold,
            "direction": captured_alert.direction
        }
        
        print("📊 Alert Message (Step 7 Format):")
        print("-" * 70)
        print(json.dumps(alert_message, indent=2))
        print("-" * 70)
        
        print("\n📋 Full Alert Details:")
        print("-" * 70)
        print(f"  ID:        {captured_alert.id}")
        print(f"  Type:      {captured_alert.type}")
        print(f"  Title:     {captured_alert.title}")
        print(f"  Message:   {captured_alert.message}")
        print(f"  Timestamp: {captured_alert.timestamp}")
        print(f"  Metric:    {captured_alert.metric}")
        print(f"  Value:     {captured_alert.value}")
        print(f"  Threshold: {captured_alert.threshold}")
        print(f"  Direction: {captured_alert.direction}")
        print("-" * 70)
        
        print("\n✅ Alert successfully triggered and matches Step 7 specification!")
    else:
        print("❌ No alert was triggered (might be in cooldown)")
    
    # Restore callbacks
    alerts.alert_callbacks = original_callbacks
    
    print("\n" + "="*70)
    print("  Run 'python test_alerts.py' to monitor live alerts via WebSocket")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(trigger_and_display_alert())
