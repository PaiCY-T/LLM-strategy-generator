"""Dataset key lookup utility for Finlab data access.

Provides correct dataset keys from the master mapping file to avoid
common errors like 'etl:monthly_revenue:revenue_yoy not exists'.
"""

import json
from typing import Dict, List, Optional


class DatasetLookup:
    """Lookup correct Finlab dataset keys from master mapping."""

    def __init__(self, mapping_file: str = "dataset_mapping.json"):
        """Initialize with dataset mapping file.

        Args:
            mapping_file: Path to dataset_mapping.json
        """
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.datasets = data['datasets']
        self.aliases = data['aliases']
        self.categories = data['categories']

    def lookup(self, search_term: str) -> Optional[str]:
        """Look up correct dataset key by name or alias.

        Args:
            search_term: Dataset name or search term

        Returns:
            Correct data.get() key or None if not found
        """
        # Direct name match
        if search_term in self.datasets:
            return self.datasets[search_term]['key']

        # Alias match
        clean_term = search_term.split('_')[0]
        if clean_term in self.aliases:
            # Return first matching key
            return self.aliases[clean_term][0]

        # Fuzzy search in names
        for name, info in self.datasets.items():
            if search_term.lower() in name.lower():
                return info['key']

        return None

    def get_category(self, category: str) -> List[Dict[str, str]]:
        """Get all datasets in a category.

        Args:
            category: Category name (price, fundamental, monthly_revenue, etc.)

        Returns:
            List of dataset info dicts
        """
        if category not in self.categories:
            return []

        return [
            {
                'name': name,
                'key': self.datasets[name]['key'],
                'type': self.datasets[name]['type']
            }
            for name in self.categories[category]
        ]

    def search(self, keyword: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search datasets by keyword.

        Args:
            keyword: Search keyword
            limit: Maximum results to return

        Returns:
            List of matching dataset info dicts
        """
        results = []
        keyword_lower = keyword.lower()

        for name, info in self.datasets.items():
            if keyword_lower in name.lower() or keyword_lower in info['key'].lower():
                results.append({
                    'name': name,
                    'key': info['key'],
                    'type': info['type']
                })

                if len(results) >= limit:
                    break

        return results

    def get_monthly_revenue_keys(self) -> Dict[str, str]:
        """Get all monthly revenue dataset keys.

        Returns:
            Dict mapping common names to correct keys
        """
        return {
            'revenue_yoy': 'monthly_revenue:去年同月增減(%)',
            'revenue_mom': 'monthly_revenue:上月比較增減(%)',
            'current_revenue': 'monthly_revenue:當月營收',
            'last_month_revenue': 'monthly_revenue:上月營收',
            'last_year_revenue': 'monthly_revenue:去年當月營收',
        }

    def validate_key(self, key: str) -> bool:
        """Check if a dataset key exists.

        Args:
            key: Dataset key to validate

        Returns:
            True if key exists in mapping
        """
        for info in self.datasets.values():
            if info['key'] == key:
                return True
        return False

    def generate_dataset_reference(self, category: Optional[str] = None) -> str:
        """Generate formatted dataset reference for prompts.

        Args:
            category: Optional category to filter (None = all common datasets)

        Returns:
            Formatted string for prompt templates
        """
        if category:
            datasets = self.get_category(category)
        else:
            # Get most commonly used datasets
            datasets = []
            for cat in ['price', 'fundamental', 'monthly_revenue', 'margin', 'institutional']:
                datasets.extend(self.get_category(cat)[:10])  # Top 10 from each

        # Format as markdown list
        lines = []
        for ds in datasets[:50]:  # Limit to 50 most important
            lines.append(f"- {ds['key']} ({ds['name']}) - Type: {ds['type']}")

        return '\n'.join(lines)


def main():
    """Test dataset lookup functionality."""
    lookup = DatasetLookup()

    print("Dataset Lookup Utility\n" + "="*60)

    # Test monthly revenue lookup
    print("\n1. Monthly Revenue Keys:")
    revenue_keys = lookup.get_monthly_revenue_keys()
    for name, key in revenue_keys.items():
        print(f"   {name:20s} -> {key}")

    # Test category search
    print("\n2. Price Datasets (first 5):")
    price_ds = lookup.get_category('price')[:5]
    for ds in price_ds:
        print(f"   {ds['key']:30s} - {ds['name']}")

    # Test keyword search
    print("\n3. Search for 'ROE':")
    roe_results = lookup.search('ROE', limit=3)
    for ds in roe_results:
        print(f"   {ds['key']:40s} - {ds['name']}")

    # Test validation
    print("\n4. Key Validation:")
    test_keys = [
        'monthly_revenue:去年同月增減(%)',
        'etl:monthly_revenue:revenue_yoy',  # Wrong key
    ]
    for key in test_keys:
        valid = lookup.validate_key(key)
        status = "✅" if valid else "❌"
        print(f"   {status} {key}")


if __name__ == '__main__':
    main()
