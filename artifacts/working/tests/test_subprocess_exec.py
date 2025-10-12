"""Test strategy execution in subprocess without finlab.login()."""

import os
import multiprocessing as mp

# Set token in environment
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'

def test_exec(queue):
    """Test execution in subprocess."""
    try:
        # MUST call finlab.login() with token in subprocess
        import os
        import finlab
        token = os.environ.get('FINLAB_API_TOKEN')
        if token:
            finlab.login(token)

        from finlab import data
        from finlab import backtest

        # Load data
        close = data.get('price:收盤價')

        # Simple strategy
        position = (close.pct_change(20) > 0.1).shift(1).is_largest(10)

        # Run backtest WITHOUT upload
        report = backtest.sim(position, resample="Q", upload=False)

        queue.put({'success': True, 'result': 'OK'})
    except Exception as e:
        import traceback
        queue.put({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

if __name__ == '__main__':
    print("Testing subprocess execution without login...")

    queue = mp.Queue()
    process = mp.Process(target=test_exec, args=(queue,))

    process.start()
    process.join(timeout=60)

    if process.is_alive():
        process.terminate()
        print("❌ Timeout!")
    else:
        result = queue.get()
        if result['success']:
            print(f"✅ Success: {result['result']}")
        else:
            print(f"❌ Error: {result['error']}")
            print(result.get('traceback', ''))
