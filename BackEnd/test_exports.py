"""
Test all export endpoints (CSV, JSON, Parquet)
"""
import requests
import json


def test_csv_export():
    """Test CSV export endpoint."""
    print("\n" + "="*70)
    print("  📊 Testing CSV Export")
    print("="*70)
    
    url = "http://localhost:8000/export/csv"
    params = {"symbol": "BTCUSDT", "limit": 10}
    
    print(f"  Request: GET {url}")
    print(f"  Params: {params}\n")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print("✅ CSV Export Successful!")
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type')}")
            print(f"  Content-Disposition: {response.headers.get('content-disposition')}")
            print(f"\n  First 500 characters:")
            print("-" * 70)
            print(response.text[:500])
            print("-" * 70)
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Error: {e}")


def test_json_export():
    """Test JSON export endpoint."""
    print("\n" + "="*70)
    print("  📊 Testing JSON Export")
    print("="*70)
    
    url = "http://localhost:8000/export/json"
    params = {"symbol": "BTCUSDT", "limit": 3}
    
    print(f"  Request: GET {url}")
    print(f"  Params: {params}\n")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print("✅ JSON Export Successful!")
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type')}")
            print(f"\n  Response (formatted):")
            print("-" * 70)
            data = response.json()
            print(json.dumps(data, indent=2))
            print("-" * 70)
            
            # Validate structure
            print("\n  Validation:")
            if "symbol" in data and "interval" in data and "records" in data:
                print("  ✅ Has symbol, interval, records")
            if data.get("records") and len(data["records"]) > 0:
                first_record = data["records"][0]
                if "ohlcv" in first_record and "analytics" in first_record:
                    print("  ✅ Records have ohlcv + analytics structure")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Error: {e}")


def test_parquet_export():
    """Test Parquet export endpoint."""
    print("\n" + "="*70)
    print("  📊 Testing Parquet Export")
    print("="*70)
    
    url = "http://localhost:8000/export/parquet"
    params = {"symbol": "BTCUSDT", "limit": 10}
    
    print(f"  Request: GET {url}")
    print(f"  Params: {params}\n")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print("✅ Parquet Export Successful!")
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type')}")
            print(f"  Content-Disposition: {response.headers.get('content-disposition')}")
            print(f"  File Size: {len(response.content)} bytes")
            
            # Try to read parquet
            try:
                import pyarrow.parquet as pq
                import io
                
                parquet_file = pq.read_table(io.BytesIO(response.content))
                print(f"\n  Parquet Schema:")
                print("-" * 70)
                print(parquet_file.schema)
                print("-" * 70)
                print(f"\n  Rows: {parquet_file.num_rows}")
                print(f"  Columns: {parquet_file.num_columns}")
                
                print(f"\n  First 3 rows:")
                print("-" * 70)
                df = parquet_file.to_pandas()
                print(df.head(3).to_string())
                print("-" * 70)
                
            except ImportError:
                print("\n  ℹ️  Install pyarrow to validate: pip install pyarrow")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  🔹 STEP 8: DATA EXPORT - Test Suite")
    print("="*70)
    print("  Testing all export endpoints...")
    print("  Make sure backend is running on http://localhost:8000")
    print("="*70)
    
    test_csv_export()
    test_json_export()
    test_parquet_export()
    
    print("\n" + "="*70)
    print("  ✅ All export tests completed!")
    print("="*70 + "\n")
