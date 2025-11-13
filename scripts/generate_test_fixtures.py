"""
Generate Test Fixtures for Template System Tests
=================================================

This script generates test fixtures from the Finlab API for use in template
system unit tests. It creates parquet files containing a representative sample
of Taiwan stock data for 10 stocks over 252 trading days (1 year).

Fixtures Generated:
-------------------
1. price:收盤價 (close price)
2. price:成交股數 (volume)
3. monthly_revenue:當月營收 (monthly revenue)
4. monthly_revenue:去年同月增減(%) (YoY revenue growth)
5. monthly_revenue:上月比較增減(%) (MoM revenue growth)
6. fundamental_features:營業利益率 (operating margin)
7. fundamental_features:ROE綜合損益 (ROE)
8. fundamental_features:資產報酬率 (ROA)
9. price_earning_ratio:殖利率(%) (dividend yield)
10. price_earning_ratio:本益比 (P/E ratio)
11. price_earning_ratio:股價淨值比 (P/B ratio)
12. internal_equity_changes:董監持有股數占比 (director holdings)

Stock Selection:
----------------
10 representative Taiwan stocks (Large Cap + Mid Cap mix):
- 2330 (TSMC - Technology)
- 2317 (Hon Hai - Technology)
- 2454 (MediaTek - Technology)
- 2303 (United Microelectronics - Technology)
- 2308 (Delta Electronics - Components)
- 2412 (Chunghwa Telecom - Telecom)
- 2882 (Cathay Financial - Finance)
- 2886 (Mega Financial - Finance)
- 2891 (CTBC Financial - Finance)
- 2892 (First Financial - Finance)

Usage:
------
    python scripts/generate_test_fixtures.py

Requirements:
-------------
- Finlab API configured with valid credentials
- Internet connection for API access
- Sufficient API rate limits (12 datasets x 1s rate limit = ~15s runtime)

Output:
-------
- Creates tests/fixtures/ directory
- Generates 12 parquet files (~400-800KB total)
- Each file contains 252 days x 10 stocks of data
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_synthetic_data(num_days: int, stocks: list, dataset_key: str) -> pd.DataFrame:
    """
    Generate synthetic test data matching Finlab data structure.

    Args:
        num_days: Number of trading days to generate
        stocks: List of stock symbols
        dataset_key: Dataset identifier for value range selection

    Returns:
        DataFrame with dates as index and stock symbols as columns
    """
    # Generate date range (business days only)
    end_date = datetime(2025, 10, 11)  # Recent date for testing
    dates = pd.bdate_range(end=end_date, periods=num_days)

    # Generate data based on dataset type
    np.random.seed(42)  # Reproducible data

    if 'price:收盤價' in dataset_key:
        # Close price: 100-500 TWD with realistic daily changes
        base_prices = np.random.uniform(100, 500, len(stocks))
        data = []
        for i in range(num_days):
            daily_change = np.random.normal(0, 0.02, len(stocks))  # 2% daily volatility
            if i == 0:
                data.append(base_prices)
            else:
                data.append(data[-1] * (1 + daily_change))
        df = pd.DataFrame(np.array(data), index=dates, columns=stocks)

    elif 'price:成交股數' in dataset_key:
        # Volume: 100k-10M shares with occasional spikes
        base_volume = np.random.uniform(100_000, 5_000_000, (num_days, len(stocks)))
        spikes = np.random.random((num_days, len(stocks))) > 0.9
        volume_data = base_volume * (1 + spikes * 5)  # 5x spike on rare days
        df = pd.DataFrame(volume_data, index=dates, columns=stocks)

    elif 'monthly_revenue:當月營收' in dataset_key:
        # Monthly revenue: 1B-50B TWD growing trend
        base_rev = np.random.uniform(1_000_000, 50_000_000, len(stocks))
        data = []
        for i in range(num_days):
            growth = np.random.normal(0.01, 0.05, len(stocks))  # 1% monthly growth
            if i == 0:
                data.append(base_rev)
            else:
                data.append(data[-1] * (1 + growth))
        df = pd.DataFrame(np.array(data), index=dates, columns=stocks)

    elif '去年同月增減(%)' in dataset_key:
        # YoY revenue growth: -20% to +40%
        df = pd.DataFrame(
            np.random.normal(10, 15, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif '上月比較增減(%)' in dataset_key:
        # MoM revenue growth: -10% to +20%
        df = pd.DataFrame(
            np.random.normal(2, 8, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif 'fundamental_features:營業利益率' in dataset_key:
        # Operating margin: 0-15%
        df = pd.DataFrame(
            np.random.uniform(0, 15, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif 'fundamental_features:ROE綜合損益' in dataset_key:
        # ROE: 5-25%
        df = pd.DataFrame(
            np.random.uniform(5, 25, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif 'fundamental_features:資產報酬率' in dataset_key:
        # ROA: 2-15%
        df = pd.DataFrame(
            np.random.uniform(2, 15, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif 'price_earning_ratio:殖利率(%)' in dataset_key:
        # Dividend yield: 2-8%
        df = pd.DataFrame(
            np.random.uniform(2, 8, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif 'price_earning_ratio:本益比' in dataset_key:
        # P/E ratio: 8-30
        df = pd.DataFrame(
            np.random.uniform(8, 30, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif 'price_earning_ratio:股價淨值比' in dataset_key:
        # P/B ratio: 0.8-3.5
        df = pd.DataFrame(
            np.random.uniform(0.8, 3.5, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    elif 'internal_equity_changes:董監持有股數占比' in dataset_key:
        # Director holdings: 5-20%
        df = pd.DataFrame(
            np.random.uniform(5, 20, (num_days, len(stocks))),
            index=dates, columns=stocks
        )

    else:
        raise ValueError(f"Unknown dataset key: {dataset_key}")

    return df


def generate_fixtures():
    """
    Generate synthetic test fixtures for template system tests.

    Creates parquet files with realistic synthetic data that matches
    Finlab data structure for testing purposes.

    Raises:
        Exception: If data generation or saving fails
    """
    # Stock selection: 10 representative Taiwan stocks
    stocks = ['2330', '2317', '2454', '2303', '2308', '2412', '2882', '2886', '2891', '2892']

    # All required datasets (12 total)
    datasets = [
        'price:收盤價',  # Close price (all templates)
        'price:成交股數',  # Volume (all templates)
        'monthly_revenue:當月營收',  # Monthly revenue (Turtle, Mastiff, Momentum)
        'monthly_revenue:去年同月增減(%)',  # YoY revenue growth (Turtle, Mastiff, Factor)
        'monthly_revenue:上月比較增減(%)',  # MoM revenue growth (Mastiff only)
        'fundamental_features:營業利益率',  # Operating margin (Turtle, Factor)
        'fundamental_features:ROE綜合損益',  # ROE (Factor only)
        'fundamental_features:資產報酬率',  # ROA (Factor only)
        'price_earning_ratio:殖利率(%)',  # Dividend yield (Turtle only)
        'price_earning_ratio:本益比',  # P/E ratio (Factor only)
        'price_earning_ratio:股價淨值比',  # P/B ratio (Factor only)
        'internal_equity_changes:董監持有股數占比',  # Director holdings (Turtle only)
    ]

    # Create output directory
    output_dir = project_root / 'tests' / 'fixtures'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating synthetic test fixtures for {len(datasets)} datasets...")
    print(f"Output directory: {output_dir}")
    print(f"Selected stocks: {', '.join(stocks)}")
    print(f"Time period: 252 trading days (1 year)")
    print()

    successful = 0
    failed = []

    for i, dataset_key in enumerate(datasets, 1):
        try:
            print(f"[{i}/{len(datasets)}] Generating {dataset_key}...", end=' ', flush=True)

            # Generate synthetic data
            data_df = generate_synthetic_data(252, stocks, dataset_key)

            # Generate safe filename (replace special characters)
            filename = dataset_key.replace(':', '_').replace('/', '_').replace('%', 'pct') + '.parquet'
            filepath = output_dir / filename

            # Save as parquet format (efficient and preserves dtypes)
            data_df.to_parquet(filepath)

            # Calculate file size
            file_size_kb = filepath.stat().st_size / 1024

            print(f"OK ({data_df.shape[0]} days, {data_df.shape[1]} stocks, {file_size_kb:.1f}KB)")
            successful += 1

        except Exception as e:
            print(f"FAILED - {e}")
            failed.append((dataset_key, str(e)))

    # Print summary
    print()
    print("=" * 70)
    print(f"Fixture Generation Complete")
    print("=" * 70)
    print(f"Successful: {successful}/{len(datasets)}")

    if failed:
        print(f"Failed: {len(failed)}")
        print("\nFailed datasets:")
        for dataset_key, error in failed:
            print(f"  - {dataset_key}: {error}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(datasets)} fixture files generated successfully!")
        print(f"Total size: {sum((output_dir / f.name).stat().st_size for f in output_dir.iterdir()) / 1024:.1f}KB")
        print(f"Location: {output_dir}")


if __name__ == '__main__':
    try:
        generate_fixtures()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
