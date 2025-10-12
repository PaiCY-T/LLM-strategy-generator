"""Data wrapper for passing preloaded datasets to sandbox processes.

This wrapper allows us to preload Finlab datasets once in the main process,
then pass them as picklable dictionaries to child processes, avoiding the
10+ minute data loading time on each sandbox execution.

Architecture:
- Main process: Loads all datasets via finlab.data.get() once
- Child processes: Receive PreloadedData wrapper with dataset dictionaries
- Wrapper: Provides data.get() interface for strategy code compatibility

Performance Impact:
- Without wrapper: 10+ minutes per iteration (fresh data load)
- With wrapper: < 1 minute per iteration (dictionary access)
"""

import pandas as pd
from typing import Dict, Any


class PreloadedData:
    """Wrapper for preloaded datasets that mimics finlab.data.get() interface.

    This class wraps a dictionary of preloaded pandas DataFrames and provides
    a get() method that strategy code can call just like finlab.data.get().

    The key insight is that dictionaries (and DataFrames) are picklable and can
    be passed between processes via multiprocessing, unlike Python module objects.

    Attributes:
        _datasets: Dictionary mapping dataset keys to pandas DataFrames

    Example:
        >>> # Main process
        >>> from finlab import data
        >>> datasets = {
        ...     'price:收盤價': data.get('price:收盤價'),
        ...     'price:成交股數': data.get('price:成交股數')
        ... }
        >>> wrapper = PreloadedData(datasets)
        >>>
        >>> # Pass to child process (pickling happens automatically)
        >>> # In child process, strategy code can use:
        >>> close = wrapper.get('price:收盤價')  # Works like data.get()
    """

    def __init__(self, datasets_dict: Dict[str, pd.DataFrame]):
        """Initialize with preloaded datasets dictionary.

        Args:
            datasets_dict: Dictionary mapping dataset keys to DataFrames
        """
        self._datasets = datasets_dict

    def get(self, key: str) -> pd.DataFrame:
        """Get dataset by key from preloaded data.

        Args:
            key: Dataset key (e.g., 'price:收盤價', 'fundamental_features:ROE稅後')

        Returns:
            pandas DataFrame for the requested dataset

        Raises:
            KeyError: If dataset was not preloaded
        """
        if key in self._datasets:
            return self._datasets[key]
        else:
            available = list(self._datasets.keys())
            raise KeyError(
                f"Dataset '{key}' not preloaded. "
                f"Available datasets: {available}"
            )

    def list_available(self) -> list:
        """List all available preloaded datasets.

        Returns:
            List of dataset keys
        """
        return list(self._datasets.keys())

    def __repr__(self) -> str:
        """String representation showing number of preloaded datasets."""
        return f"PreloadedData({len(self._datasets)} datasets)"


def load_common_datasets() -> Dict[str, pd.DataFrame]:
    """Load all commonly used datasets from Finlab API.

    This function loads a curated set of datasets that cover most strategy needs:
    - Price data (OHLC, volume, trading value)
    - Fundamental data (ROE, P/E ratio, profit margin)
    - Revenue data (YoY growth)
    - Institutional investor data (foreign holdings)

    This should be called ONCE in the main process at startup.

    Returns:
        Dictionary mapping dataset keys to pandas DataFrames

    Raises:
        ImportError: If finlab is not installed
        Exception: If data loading fails

    Note:
        This function may take 10+ minutes to complete as it downloads
        all historical data for Taiwan stocks.
    """
    from finlab import data

    datasets = {}

    # Only load CORE datasets that have been verified to work in successful iterations
    # These are the 6 most frequently used datasets from previous runs

    print("   Loading price data...")
    datasets['price:收盤價'] = data.get('price:收盤價')
    datasets['price:成交股數'] = data.get('price:成交股數')
    datasets['price:成交金額'] = data.get('price:成交金額')

    print("   Loading fundamental data...")
    datasets['fundamental_features:ROE稅後'] = data.get('fundamental_features:ROE稅後')

    print("   Loading valuation data...")
    datasets['price_earning_ratio:本益比'] = data.get('price_earning_ratio:本益比')
    datasets['price_earning_ratio:股價淨值比'] = data.get('price_earning_ratio:股價淨值比')

    print("   Loading revenue data...")
    datasets['monthly_revenue:去年同月增減(%)'] = data.get('monthly_revenue:去年同月增減(%)')

    print("   Loading financial statement data...")
    datasets['financial_statement:每股盈餘'] = data.get('financial_statement:每股盈餘')

    print("   Loading institutional investor data...")
    datasets['institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)'] = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

    print(f"   ✅ Loaded {len(datasets)} datasets")

    return datasets
