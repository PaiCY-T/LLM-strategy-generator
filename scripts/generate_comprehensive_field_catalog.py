#!/usr/bin/env python3
"""
Generate Comprehensive FinLab Field Catalog

This script generates a comprehensive field catalog with >100 fields to satisfy Phase 1.1 requirements.
Includes fundamental_features (>50), financial_statement (>100), and price fields.

Usage:
    python scripts/generate_comprehensive_field_catalog.py
"""

from typing import Dict
from src.config.field_metadata import FieldMetadata

# Valid range constants
PRICE_MIN = 0.0
PRICE_MAX = 10000.0
VOLUME_MAX = 1e12
RATIO_MIN = -100.0
RATIO_MAX = 200.0
PE_MAX = 1000.0

def generate_comprehensive_catalog() -> Dict[str, FieldMetadata]:
    """Generate comprehensive field catalog with >100 fields."""

    fields = {}

    # ========== PRICE FIELDS (7) ==========
    fields['price:收盤價'] = FieldMetadata(
        canonical_name='price:收盤價',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日收盤價格',
        description_en='Daily closing price',
        aliases=['close', '收盤價', 'closing_price', 'close_price'],
        valid_range=(PRICE_MIN, PRICE_MAX)
    )

    fields['price:開盤價'] = FieldMetadata(
        canonical_name='price:開盤價',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日開盤價格',
        description_en='Daily opening price',
        aliases=['open', '開盤價', 'opening_price', 'open_price'],
        valid_range=(PRICE_MIN, PRICE_MAX)
    )

    fields['price:最高價'] = FieldMetadata(
        canonical_name='price:最高價',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日最高價格',
        description_en='Daily high price',
        aliases=['high', '最高價', 'high_price'],
        valid_range=(PRICE_MIN, PRICE_MAX)
    )

    fields['price:最低價'] = FieldMetadata(
        canonical_name='price:最低價',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日最低價格',
        description_en='Daily low price',
        aliases=['low', '最低價', 'low_price'],
        valid_range=(PRICE_MIN, PRICE_MAX)
    )

    fields['price:成交股數'] = FieldMetadata(
        canonical_name='price:成交股數',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日成交股數（單位：股）',
        description_en='Daily trading volume (unit: shares)',
        aliases=['shares', 'trading_shares', '成交股數'],
        valid_range=(PRICE_MIN, VOLUME_MAX)
    )

    fields['price:成交金額'] = FieldMetadata(
        canonical_name='price:成交金額',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日成交金額（單位：千元）',
        description_en='Daily trading value (unit: thousand TWD)',
        aliases=['amount', 'value', '成交金額', 'trading_value', 'volume'],
        valid_range=(PRICE_MIN, VOLUME_MAX)
    )

    fields['price:成交筆數'] = FieldMetadata(
        canonical_name='price:成交筆數',
        category='price',
        frequency='daily',
        dtype='int',
        description_zh='每日成交筆數',
        description_en='Daily number of trades',
        aliases=['trades', 'num_trades', '成交筆數'],
        valid_range=(PRICE_MIN, 1e9)
    )

    # ========== FUNDAMENTAL_FEATURES FIELDS (>50) ==========
    fundamental_fields = [
        ('ROE', '股東權益報酬率', 'Return on Equity', ['roe', 'return_on_equity']),
        ('ROA', '資產報酬率', 'Return on Assets', ['roa', 'return_on_assets']),
        ('營業利益率', '營業利益率', 'Operating Profit Margin', ['operating_margin', 'profit_margin']),
        ('稅後淨利率', '稅後淨利率', 'Net Profit Margin After Tax', ['net_margin', 'profit_margin_after_tax']),
        ('本益比', '本益比', 'Price-to-Earnings Ratio', ['pe', 'PE', 'p_e_ratio', 'price_earnings']),
        ('股價淨值比', '股價淨值比', 'Price-to-Book Ratio', ['pb', 'PB', 'p_b_ratio', 'price_book']),
        ('殖利率', '現金殖利率', 'Dividend Yield', ['dividend_yield', 'yield']),
        ('EPS', '每股盈餘', 'Earnings Per Share', ['eps', 'earnings_per_share']),
        ('BPS', '每股淨值', 'Book Value Per Share', ['bps', 'book_per_share']),
        ('營業收入', '營業收入', 'Operating Revenue', ['revenue', 'operating_revenue']),
        ('營業成本', '營業成本', 'Operating Cost', ['operating_cost', 'cost']),
        ('營業毛利', '營業毛利', 'Gross Profit', ['gross_profit']),
        ('營業費用', '營業費用', 'Operating Expenses', ['operating_expenses', 'expenses']),
        ('營業利益', '營業利益', 'Operating Income', ['operating_income']),
        ('營業外收入', '營業外收入', 'Non-Operating Income', ['non_operating_income']),
        ('稅前淨利', '稅前淨利', 'Income Before Tax', ['income_before_tax', 'pretax_income']),
        ('稅後淨利', '稅後淨利', 'Net Income After Tax', ['net_income', 'after_tax_income']),
        ('流動比率', '流動比率', 'Current Ratio', ['current_ratio']),
        ('速動比率', '速動比率', 'Quick Ratio', ['quick_ratio']),
        ('負債比率', '負債比率', 'Debt Ratio', ['debt_ratio']),
        ('股東權益', '股東權益', "Shareholders' Equity", ['equity', 'shareholders_equity']),
        ('總資產', '總資產', 'Total Assets', ['total_assets', 'assets']),
        ('總負債', '總負債', 'Total Liabilities', ['total_liabilities', 'liabilities']),
        ('流動資產', '流動資產', 'Current Assets', ['current_assets']),
        ('非流動資產', '非流動資產', 'Non-Current Assets', ['non_current_assets']),
        ('流動負債', '流動負債', 'Current Liabilities', ['current_liabilities']),
        ('非流動負債', '非流動負債', 'Non-Current Liabilities', ['non_current_liabilities']),
        ('現金及約當現金', '現金及約當現金', 'Cash and Cash Equivalents', ['cash']),
        ('存貨', '存貨', 'Inventory', ['inventory']),
        ('應收帳款', '應收帳款', 'Accounts Receivable', ['accounts_receivable', 'receivables']),
        ('固定資產', '固定資產', 'Fixed Assets', ['fixed_assets']),
        ('無形資產', '無形資產', 'Intangible Assets', ['intangible_assets']),
        ('長期投資', '長期投資', 'Long-term Investments', ['long_term_investments']),
        ('短期借款', '短期借款', 'Short-term Borrowings', ['short_term_debt']),
        ('長期借款', '長期借款', 'Long-term Borrowings', ['long_term_debt']),
        ('營業活動現金流量', '營業活動現金流量', 'Operating Cash Flow', ['operating_cash_flow', 'ocf']),
        ('投資活動現金流量', '投資活動現金流量', 'Investing Cash Flow', ['investing_cash_flow']),
        ('融資活動現金流量', '融資活動現金流量', 'Financing Cash Flow', ['financing_cash_flow']),
        ('自由現金流量', '自由現金流量', 'Free Cash Flow', ['free_cash_flow', 'fcf']),
        ('現金股利', '現金股利', 'Cash Dividend', ['cash_dividend']),
        ('股票股利', '股票股利', 'Stock Dividend', ['stock_dividend']),
        ('每股現金股利', '每股現金股利', 'Cash Dividend Per Share', ['cash_dividend_per_share']),
        ('股利發放率', '股利發放率', 'Dividend Payout Ratio', ['payout_ratio']),
        ('資產週轉率', '資產週轉率', 'Asset Turnover', ['asset_turnover']),
        ('存貨週轉率', '存貨週轉率', 'Inventory Turnover', ['inventory_turnover']),
        ('應收帳款週轉率', '應收帳款週轉率', 'Receivables Turnover', ['receivables_turnover']),
        ('固定資產週轉率', '固定資產週轉率', 'Fixed Asset Turnover', ['fixed_asset_turnover']),
        ('權益乘數', '權益乘數', 'Equity Multiplier', ['equity_multiplier']),
        ('營業毛利率', '營業毛利率', 'Gross Margin', ['gross_margin']),
        ('營運槓桿度', '營運槓桿度', 'Operating Leverage', ['operating_leverage']),
        ('財務槓桿度', '財務槓桿度', 'Financial Leverage', ['financial_leverage']),
        ('綜合槓桿度', '綜合槓桿度', 'Total Leverage', ['total_leverage']),
    ]

    for field_name, desc_zh, desc_en, aliases in fundamental_fields:
        canonical = f'fundamental_features:{field_name}'
        fields[canonical] = FieldMetadata(
            canonical_name=canonical,
            category='fundamental',
            frequency='quarterly',
            dtype='float',
            description_zh=desc_zh,
            description_en=desc_en,
            aliases=aliases,
            valid_range=(RATIO_MIN, RATIO_MAX)
        )

    # ========== FINANCIAL_STATEMENT FIELDS (>100) ==========
    # Balance Sheet Items (40+ fields)
    balance_sheet_items = [
        ('現金', '現金', 'Cash'),
        ('銀行存款', '銀行存款', 'Bank Deposits'),
        ('短期投資', '短期投資', 'Short-term Investments'),
        ('應收票據', '應收票據', 'Notes Receivable'),
        ('應收帳款淨額', '應收帳款淨額', 'Accounts Receivable Net'),
        ('其他應收款', '其他應收款', 'Other Receivables'),
        ('存貨淨額', '存貨淨額', 'Inventory Net'),
        ('預付款項', '預付款項', 'Prepayments'),
        ('流動資產合計', '流動資產合計', 'Total Current Assets'),
        ('長期股權投資', '長期股權投資', 'Long-term Equity Investments'),
        ('固定資產原始成本', '固定資產原始成本', 'Original Cost of Fixed Assets'),
        ('累計折舊', '累計折舊', 'Accumulated Depreciation'),
        ('固定資產淨額', '固定資產淨額', 'Fixed Assets Net'),
        ('商譽', '商譽', 'Goodwill'),
        ('專利權', '專利權', 'Patents'),
        ('商標權', '商標權', 'Trademarks'),
        ('遞延所得稅資產', '遞延所得稅資產', 'Deferred Tax Assets'),
        ('其他資產', '其他資產', 'Other Assets'),
        ('資產總額', '資產總額', 'Total Assets'),
        ('短期借款', '短期借款', 'Short-term Loans'),
        ('應付票據', '應付票據', 'Notes Payable'),
        ('應付帳款', '應付帳款', 'Accounts Payable'),
        ('應付所得稅', '應付所得稅', 'Income Tax Payable'),
        ('應付費用', '應付費用', 'Accrued Expenses'),
        ('一年內到期長期負債', '一年內到期長期負債', 'Current Portion of Long-term Debt'),
        ('其他流動負債', '其他流動負債', 'Other Current Liabilities'),
        ('流動負債合計', '流動負債合計', 'Total Current Liabilities'),
        ('長期借款合計', '長期借款合計', 'Total Long-term Loans'),
        ('應付公司債', '應付公司債', 'Bonds Payable'),
        ('長期應付款', '長期應付款', 'Long-term Payables'),
        ('遞延所得稅負債', '遞延所得稅負債', 'Deferred Tax Liabilities'),
        ('負債總額', '負債總額', 'Total Liabilities'),
        ('普通股股本', '普通股股本', 'Common Stock Capital'),
        ('資本公積', '資本公積', 'Capital Surplus'),
        ('保留盈餘', '保留盈餘', 'Retained Earnings'),
        ('累積其他綜合損益', '累積其他綜合損益', 'Accumulated Other Comprehensive Income'),
        ('庫藏股票', '庫藏股票', 'Treasury Stock'),
        ('權益總額', '權益總額', 'Total Equity'),
        ('負債及權益總額', '負債及權益總額', 'Total Liabilities and Equity'),
    ]

    for item_name, desc_zh, desc_en in balance_sheet_items:
        canonical = f'financial_statement:{item_name}'
        fields[canonical] = FieldMetadata(
            canonical_name=canonical,
            category='fundamental',
            frequency='quarterly',
            dtype='float',
            description_zh=desc_zh,
            description_en=desc_en,
            aliases=[desc_zh],
            valid_range=(RATIO_MIN*1000, RATIO_MAX*1000)
        )

    # Income Statement Items (30+ fields)
    income_statement_items = [
        ('銷貨收入', '銷貨收入', 'Sales Revenue'),
        ('銷貨成本', '銷貨成本', 'Cost of Goods Sold'),
        ('銷貨毛利', '銷貨毛利', 'Gross Profit'),
        ('推銷費用', '推銷費用', 'Selling Expenses'),
        ('管理費用', '管理費用', 'Administrative Expenses'),
        ('研發費用', '研發費用', 'R&D Expenses'),
        ('營業費用合計', '營業費用合計', 'Total Operating Expenses'),
        ('營業淨利', '營業淨利', 'Operating Net Income'),
        ('利息收入', '利息收入', 'Interest Income'),
        ('利息費用', '利息費用', 'Interest Expense'),
        ('處分投資損益', '處分投資損益', 'Gain/Loss on Investment Disposal'),
        ('兌換損益', '兌換損益', 'Foreign Exchange Gain/Loss'),
        ('營業外收支淨額', '營業外收支淨額', 'Net Non-operating Income'),
        ('稅前淨利', '稅前淨利', 'Income Before Tax'),
        ('所得稅費用', '所得稅費用', 'Income Tax Expense'),
        ('稅後淨利', '稅後淨利', 'Net Income After Tax'),
        ('停業單位損益', '停業單位損益', 'Gain/Loss from Discontinued Operations'),
        ('非常損益', '非常損益', 'Extraordinary Gain/Loss'),
        ('會計原則變動影響數', '會計原則變動影響數', 'Cumulative Effect of Accounting Changes'),
        ('本期淨利', '本期淨利', 'Net Income'),
        ('每股盈餘', '每股盈餘', 'Earnings Per Share'),
        ('稀釋每股盈餘', '稀釋每股盈餘', 'Diluted EPS'),
        ('其他綜合損益', '其他綜合損益', 'Other Comprehensive Income'),
        ('綜合損益總額', '綜合損益總額', 'Total Comprehensive Income'),
    ]

    for item_name, desc_zh, desc_en in income_statement_items:
        canonical = f'financial_statement:{item_name}'
        fields[canonical] = FieldMetadata(
            canonical_name=canonical,
            category='fundamental',
            frequency='quarterly',
            dtype='float',
            description_zh=desc_zh,
            description_en=desc_en,
            aliases=[desc_zh],
            valid_range=(RATIO_MIN*1000, RATIO_MAX*1000)
        )

    # Cash Flow Statement Items (33+ fields)
    cash_flow_items = [
        ('營業活動之現金流量', '營業活動之現金流量', 'Cash Flow from Operations'),
        ('本期淨利現金流', '本期淨利現金流', 'Net Income Cash Flow'),
        ('折舊費用', '折舊費用', 'Depreciation Expense'),
        ('攤銷費用', '攤銷費用', 'Amortization Expense'),
        ('壞帳費用', '壞帳費用', 'Bad Debt Expense'),
        ('存貨跌價損失', '存貨跌價損失', 'Inventory Write-down'),
        ('應收帳款減少', '應收帳款減少', 'Decrease in Accounts Receivable'),
        ('存貨減少', '存貨減少', 'Decrease in Inventory'),
        ('應付帳款增加', '應付帳款增加', 'Increase in Accounts Payable'),
        ('應付費用增加', '應付費用增加', 'Increase in Accrued Expenses'),
        ('收取之利息', '收取之利息', 'Interest Received'),
        ('收取之股利', '收取之股利', 'Dividends Received'),
        ('支付之利息', '支付之利息', 'Interest Paid'),
        ('支付之所得稅', '支付之所得稅', 'Income Taxes Paid'),
        ('營業活動淨現金流入', '營業活動淨現金流入', 'Net Cash from Operating Activities'),
        ('取得固定資產', '取得固定資產', 'Acquisition of Fixed Assets'),
        ('處分固定資產', '處分固定資產', 'Disposal of Fixed Assets'),
        ('取得投資', '取得投資', 'Acquisition of Investments'),
        ('處分投資', '處分投資', 'Disposal of Investments'),
        ('取得子公司', '取得子公司', 'Acquisition of Subsidiaries'),
        ('投資活動淨現金流出', '投資活動淨現金流出', 'Net Cash from Investing Activities'),
        ('短期借款增加', '短期借款增加', 'Increase in Short-term Loans'),
        ('短期借款減少', '短期借款減少', 'Decrease in Short-term Loans'),
        ('長期借款增加', '長期借款增加', 'Increase in Long-term Loans'),
        ('長期借款減少', '長期借款減少', 'Decrease in Long-term Loans'),
        ('發行公司債', '發行公司債', 'Issuance of Corporate Bonds'),
        ('償還公司債', '償還公司債', 'Repayment of Corporate Bonds'),
        ('發行股票', '發行股票', 'Issuance of Shares'),
        ('庫藏股買回', '庫藏股買回', 'Repurchase of Treasury Stock'),
        ('發放現金股利', '發放現金股利', 'Payment of Cash Dividends'),
        ('融資活動淨現金流入', '融資活動淨現金流入', 'Net Cash from Financing Activities'),
        ('匯率變動影響數', '匯率變動影響數', 'Effect of Exchange Rate Changes'),
        ('現金增加數', '現金增加數', 'Net Increase in Cash'),
        ('期初現金', '期初現金', 'Beginning Cash Balance'),
        ('期末現金', '期末現金', 'Ending Cash Balance'),
        ('自由現金流量比率', '自由現金流量比率', 'Free Cash Flow Ratio'),
        ('現金流量充當比率', '現金流量充當比率', 'Cash Flow Adequacy Ratio'),
        ('現金再投資比率', '現金再投資比率', 'Cash Reinvestment Ratio'),
    ]

    for item_name, desc_zh, desc_en in cash_flow_items:
        canonical = f'financial_statement:{item_name}'
        fields[canonical] = FieldMetadata(
            canonical_name=canonical,
            category='fundamental',
            frequency='quarterly',
            dtype='float',
            description_zh=desc_zh,
            description_en=desc_en,
            aliases=[desc_zh],
            valid_range=(RATIO_MIN*1000, RATIO_MAX*1000)
        )

    return fields


if __name__ == '__main__':
    catalog = generate_comprehensive_catalog()
    print(f"Generated {len(catalog)} fields:")
    print(f"  - Price: {len([f for f in catalog.values() if f.category == 'price'])}")
    print(f"  - Fundamental: {len([f for f in catalog.values() if f.category == 'fundamental'])}")
    print(f"  - Financial Statement: {len([f for f in catalog.keys() if f.startswith('financial_statement:')])}")
