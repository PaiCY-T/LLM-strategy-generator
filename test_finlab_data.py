"""Test finlab data initialization and access.

Attempts to initialize finlab with API token and load sample data.
"""

import os
import sys

# Set API token from environment
api_token = os.environ.get('FINLAB_API_TOKEN')
if not api_token:
    print("❌ FINLAB_API_TOKEN not set")
    sys.exit(1)

print(f"✅ API token found: {api_token[:20]}...")

# Try to import and initialize finlab
try:
    print("\n[1/3] Importing finlab...")
    import finlab
    print(f"✅ finlab version: {finlab.__version__}")
except ImportError as e:
    print(f"❌ Failed to import finlab: {e}")
    print("\nTry: pip install finlab")
    sys.exit(1)

# Try to set API token programmatically
try:
    print("\n[2/3] Setting API token...")
    # Try different methods to set token

    # Method 1: Direct token assignment (finlab 1.x)
    try:
        finlab.login(api_token)
        print("✅ Method 1: finlab.login() succeeded")
    except AttributeError:
        pass
    except Exception as e:
        print(f"⚠️  Method 1 failed: {e}")

    # Method 2: Environment variable (should already be set)
    os.environ['FINLAB_API_TOKEN'] = api_token
    print("✅ Method 2: Environment variable set")

except Exception as e:
    print(f"❌ Token setup failed: {e}")

# Try to access data
try:
    print("\n[3/3] Testing data access...")

    # Import data module
    from finlab import data
    print("✅ finlab.data imported")

    # Try to get a simple dataset
    print("\nAttempting to load price:收盤價...")
    close = data.get('price:收盤價')

    if close is not None:
        print(f"✅ Data loaded successfully!")
        print(f"   Shape: {close.shape}")
        print(f"   Date range: {close.index[0]} to {close.index[-1]}")
        print(f"   Stocks: {close.shape[1]}")
    else:
        print("❌ data.get() returned None")

except Exception as e:
    print(f"❌ Data access failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("FINLAB DATA TEST COMPLETE")
print("="*60)
