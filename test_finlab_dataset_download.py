#!/usr/bin/env python3
"""
FinLab 資料集下載與快取驗證測試
===================================

目的：
1. 逐一從 FinLab 下載 CSV 中列出的 307 個資料集
2. 驗證每個資料集都可以正常下載
3. 測試 DataCache 系統是否能作為快取使用
4. 生成詳細的下載報告和統計

使用現有組件：
- src/templates/data_cache.py - 資料快取系統
- src/backtest/finlab_authenticator.py - Session 驗證
"""

import csv
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from templates.data_cache import DataCache
from backtest.finlab_authenticator import verify_finlab_session


def load_csv_datasets(csv_path: str) -> List[Dict[str, str]]:
    """
    從 CSV 載入所有資料集定義

    Returns:
        List of dict with keys: 資料集名稱, 下載方式及key, 數據類型
    """
    datasets = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            datasets.append({
                '名稱': row['資料集名稱'],
                'key': row['下載方式及key'],
                '類型': row['數據類型']
            })

    return datasets


def extract_finlab_key(download_key: str) -> Tuple[str, str]:
    """
    從下載方式提取 FinLab data.get() 的 key

    Args:
        download_key: CSV 中的下載方式

    Returns:
        (key_type, finlab_key)
        key_type: 'etl', 'data.get', 'other'
        finlab_key: 實際的 key (e.g., 'price:收盤價')

    Examples:
        'etl:adj_close' → ('etl', 'etl:adj_close')
        "data.get('price:收盤價')" → ('data.get', 'price:收盤價')
    """
    if download_key.startswith('etl:'):
        return 'etl', download_key

    elif download_key.startswith('data.get('):
        # Extract key from data.get('key') format
        # data.get('price:收盤價') → price:收盤價
        key = download_key.split("'")[1] if "'" in download_key else None
        if key:
            return 'data.get', key
        else:
            return 'other', download_key

    else:
        return 'other', download_key


def test_dataset_download(cache: DataCache, key: str, name: str,
                          verbose: bool = True) -> Dict[str, Any]:
    """
    測試單一資料集下載

    Returns:
        結果字典包含：
        - success: bool
        - key: str
        - name: str
        - shape: tuple or None
        - error: str or None
        - load_time: float
        - cache_hit: bool (第二次測試時是否從快取讀取)
    """
    result = {
        'success': False,
        'key': key,
        'name': name,
        'shape': None,
        'error': None,
        'load_time': 0.0,
        'cache_hit': False
    }

    try:
        # 第一次下載
        start_time = time.time()
        data = cache.get(key, verbose=False)
        load_time = time.time() - start_time

        if data is None:
            result['error'] = "data.get() returned None"
            if verbose:
                print(f"  ❌ {name}: returned None")
            return result

        # 檢查 shape
        if hasattr(data, 'shape'):
            result['shape'] = data.shape
            result['load_time'] = load_time
            result['success'] = True

            if verbose:
                print(f"  ✅ {name}: {data.shape} ({load_time:.2f}s)")
        else:
            result['error'] = f"No shape attribute (type: {type(data).__name__})"
            if verbose:
                print(f"  ⚠️  {name}: No shape (type: {type(data).__name__})")

        # 測試快取 - 第二次讀取應該極快
        cache_start = time.time()
        cached_data = cache.get(key, verbose=False)
        cache_time = time.time() - cache_start

        # 快取命中應該 <0.01s
        result['cache_hit'] = cache_time < 0.01

        if verbose and result['cache_hit']:
            print(f"     💾 Cache hit! ({cache_time*1000:.1f}ms)")

        return result

    except Exception as e:
        result['error'] = f"{type(e).__name__}: {str(e)}"
        if verbose:
            print(f"  ❌ {name}: {result['error']}")
        return result


def main():
    csv_path = "/mnt/c/Users/jnpi/ML4T/epic-finlab-data-downloader/example/finlab_database_cleaned.csv"
    output_dir = Path("experiments/finlab_data_verification")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("FinLab 資料集下載與快取驗證測試")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: 驗證 FinLab session
    print("Step 1: 驗證 FinLab Session")
    print("-" * 80)
    status = verify_finlab_session(verbose=False)

    if not status.is_authenticated:
        print("❌ FinLab session 未正確驗證！")
        print(f"錯誤: {status.error_message}")
        for diag in status.diagnostics:
            print(f"  {diag}")
        return 1

    print("✅ FinLab session 驗證成功！\n")

    # Step 2: 載入資料集清單
    print("Step 2: 載入 CSV 資料集清單")
    print("-" * 80)
    datasets = load_csv_datasets(csv_path)
    print(f"✅ 載入 {len(datasets)} 個資料集定義\n")

    # Step 3: 取得快取實例
    print("Step 3: 初始化 DataCache")
    print("-" * 80)
    cache = DataCache.get_instance()
    print(f"✅ DataCache 實例已就緒\n")

    # Step 4: 逐一測試下載
    print("Step 4: 逐一下載並驗證資料集")
    print("-" * 80)
    print(f"開始下載 {len(datasets)} 個資料集...\n")

    results = []
    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, dataset in enumerate(datasets, 1):
        name = dataset['名稱']
        download_key = dataset['key']
        data_type = dataset['類型']

        print(f"[{i}/{len(datasets)}] {name}")

        # 提取 FinLab key
        key_type, finlab_key = extract_finlab_key(download_key)

        if key_type == 'other':
            print(f"  ⏭️  跳過 (無法解析的格式: {download_key})")
            skip_count += 1
            results.append({
                'index': i,
                'name': name,
                'key': download_key,
                'type': data_type,
                'key_type': key_type,
                'success': False,
                'skipped': True,
                'error': 'Unsupported format'
            })
            continue

        # 測試下載
        result = test_dataset_download(cache, finlab_key, name, verbose=True)
        result['index'] = i
        result['type'] = data_type
        result['key_type'] = key_type
        result['download_key'] = download_key

        if result['success']:
            success_count += 1
        else:
            fail_count += 1

        results.append(result)

        # 每10個資料集顯示進度
        if i % 10 == 0:
            print(f"\n進度: {i}/{len(datasets)} ({i/len(datasets)*100:.1f}%)")
            print(f"成功: {success_count}, 失敗: {fail_count}, 跳過: {skip_count}\n")

    # Step 5: 統計與報告
    print("\n" + "=" * 80)
    print("測試完成 - 統計報告")
    print("=" * 80)

    cache_stats = cache.get_stats()

    print(f"\n資料集下載統計:")
    print(f"  總數:   {len(datasets)}")
    print(f"  成功:   {success_count} ({success_count/len(datasets)*100:.1f}%)")
    print(f"  失敗:   {fail_count} ({fail_count/len(datasets)*100:.1f}%)")
    print(f"  跳過:   {skip_count} ({skip_count/len(datasets)*100:.1f}%)")

    print(f"\nDataCache 統計:")
    print(f"  快取大小:     {cache_stats['cache_size']} 個資料集")
    print(f"  快取命中率:   {cache_stats['hit_rate']:.2%}")
    print(f"  總請求次數:   {cache_stats['total_requests']}")
    print(f"  平均載入時間: {cache_stats['avg_load_time']:.2f}秒")
    print(f"  總載入時間:   {cache_stats['total_load_time']:.2f}秒")

    # 失敗的資料集
    if fail_count > 0:
        print(f"\n失敗的資料集 ({fail_count}):")
        for result in results:
            if not result['success'] and not result.get('skipped', False):
                print(f"  ❌ {result['name']}")
                print(f"     Key: {result['key']}")
                print(f"     錯誤: {result['error']}")

    # Step 6: 儲存結果
    print(f"\nStep 6: 儲存測試結果")
    print("-" * 80)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 詳細結果 JSON
    results_file = output_dir / f"dataset_download_results_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_datasets': len(datasets),
            'success_count': success_count,
            'fail_count': fail_count,
            'skip_count': skip_count,
            'cache_stats': cache_stats,
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ 詳細結果已儲存: {results_file}")

    # 簡要統計 TXT
    summary_file = output_dir / f"dataset_download_summary_{timestamp}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("FinLab 資料集下載驗證 - 摘要報告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"總資料集: {len(datasets)}\n")
        f.write(f"成功下載: {success_count} ({success_count/len(datasets)*100:.1f}%)\n")
        f.write(f"下載失敗: {fail_count} ({fail_count/len(datasets)*100:.1f}%)\n")
        f.write(f"跳過項目: {skip_count} ({skip_count/len(datasets)*100:.1f}%)\n\n")
        f.write(f"DataCache 性能:\n")
        f.write(f"  快取大小: {cache_stats['cache_size']}\n")
        f.write(f"  命中率: {cache_stats['hit_rate']:.2%}\n")
        f.write(f"  平均載入時間: {cache_stats['avg_load_time']:.2f}s\n\n")

        if fail_count > 0:
            f.write(f"失敗的資料集:\n")
            for result in results:
                if not result['success'] and not result.get('skipped', False):
                    f.write(f"  - {result['name']} ({result['key']})\n")
                    f.write(f"    錯誤: {result['error']}\n")

    print(f"✅ 摘要報告已儲存: {summary_file}")

    print("\n" + "=" * 80)
    print("測試完成！")
    print("=" * 80)

    # 結論
    print("\n📊 結論:")
    if success_count >= len(datasets) * 0.95:
        print("  ✅ 優秀！95%+ 資料集可正常下載")
    elif success_count >= len(datasets) * 0.80:
        print("  ⚠️  良好，但有部分資料集無法下載")
    else:
        print("  ❌ 警告：大量資料集無法下載")

    if cache_stats['hit_rate'] > 0.3:
        print("  ✅ DataCache 系統運作正常，可作為快取使用")
    else:
        print("  ⚠️  DataCache 快取命中率偏低")

    return 0 if success_count >= len(datasets) * 0.80 else 1


if __name__ == "__main__":
    sys.exit(main())
