import os
import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files import File
from databank.models import Category, Dataset, UserProfile
from databank.utils import validate_csv_file


CATEGORIES_DEF = [
    {
        'name': 'Stock Market',
        'description': 'Equities, indices, daily price action, moving averages, trading volumes, and historical company valuations.',
        'icon_class': 'bi-graph-up-arrow',
    },
    {
        'name': 'Agriculture',
        'description': 'Commodity spot prices, seasonal crop yields, weather impact metrics, fertilizer consumption, and agricultural trade.',
        'icon_class': 'bi-tree',
    },
    {
        'name': 'Real Estate',
        'description': 'Property price indices, rental yields, commercial leasing rates, inventory levels, and housing mortgage benchmarks.',
        'icon_class': 'bi-buildings',
    },
    {
        'name': 'Cryptocurrency',
        'description': 'Digital asset price time-series, liquidity depth, on-chain metrics, 24-hour volumes, and market capitalization.',
        'icon_class': 'bi-currency-bitcoin',
    },
    {
        'name': 'Business and Economics',
        'description': 'Macroeconomic indicators, GDP growth trajectories, inflation trends, central bank interest rates, and retail indices.',
        'icon_class': 'bi-briefcase',
    },
    {
        'name': 'Other',
        'description': 'Cross-sector datasets, exploratory market surveys, energy commodities, logistics, and alternative financial metrics.',
        'icon_class': 'bi-grid-3x3-gap',
    },
]

SAMPLE_CSVS = {
    'stock_market_top50.csv': {
        'headers': ['Date', 'Ticker', 'Company_Name', 'Sector', 'Open', 'High', 'Low', 'Close', 'Volume'],
        'rows': [
            ['2024-01-02', 'AAPL', 'Apple Inc', 'Technology', '187.15', '188.44', '183.89', '185.64', '82488700'],
            ['2024-01-03', 'AAPL', 'Apple Inc', 'Technology', '184.22', '185.88', '183.43', '184.25', '58414500'],
            ['2024-01-04', 'MSFT', 'Microsoft Corp', 'Technology', '370.67', '373.87', '370.51', '373.10', '27645300'],
            ['2024-01-05', 'MSFT', 'Microsoft Corp', 'Technology', '369.01', '372.14', '366.50', '367.75', '20988300'],
            ['2024-01-08', 'NVDA', 'NVIDIA Corp', 'Semiconductors', '495.12', '522.75', '494.79', '522.53', '64251000'],
            ['2024-01-09', 'NVDA', 'NVIDIA Corp', 'Semiconductors', '524.01', '543.25', '523.50', '531.40', '77312200'],
            ['2024-01-10', 'AMZN', 'Amazon.com Inc', 'Consumer Discretionary', '152.06', '154.42', '151.88', '153.73', '44421800'],
            ['2024-01-11', 'GOOGL', 'Alphabet Inc', 'Communication', '141.65', '143.88', '141.10', '142.08', '24100500'],
            ['2024-01-12', 'JPM', 'JPMorgan Chase', 'Financials', '171.18', '173.04', '168.90', '170.10', '19875400'],
            ['2024-01-16', 'TSLA', 'Tesla Inc', 'Automotive', '215.10', '223.49', '212.18', '219.91', '115356000'],
            ['2024-01-17', 'META', 'Meta Platforms', 'Technology', '370.00', '375.90', '367.51', '368.37', '21153000'],
            ['2024-01-18', 'BRK.B', 'Berkshire Hathaway', 'Financials', '362.45', '363.80', '360.20', '361.50', '3250000'],
            ['2024-01-19', 'V', 'Visa Inc', 'Financials', '264.30', '266.10', '263.15', '265.80', '5840000'],
            ['2024-01-22', 'WMT', 'Walmart Inc', 'Consumer Staples', '161.20', '162.70', '160.85', '162.15', '6120000'],
            ['2024-01-23', 'LLY', 'Eli Lilly and Co', 'Healthcare', '628.50', '635.00', '624.10', '633.20', '2890000'],
        ],
        'title': 'S&P 500 Blue-Chip Daily Price and Volume Matrix (2024)',
        'category': 'Stock Market',
        'source': 'NYSE / NASDAQ Market Data Feed via Financial Modeling Prep',
        'description': 'Curated daily trading data for top large-cap equities covering price ranges (open, high, low, close) and trading volumes. Ideal for technical analysis, volatility modeling, and portfolio backtesting.',
        'is_public': True,
    },
    'agriculture_crop_yields.csv': {
        'headers': ['Year', 'Region_State', 'Crop', 'Season', 'Area_Thousand_Ha', 'Production_Thousand_Tonnes', 'Yield_Kg_Per_Ha'],
        'rows': [
            ['2023', 'Punjab', 'Wheat', 'Rabi', '3500.5', '17850.0', '5100'],
            ['2023', 'Haryana', 'Wheat', 'Rabi', '2550.0', '12240.0', '4800'],
            ['2023', 'Madhya Pradesh', 'Soybean', 'Kharif', '5400.2', '6480.0', '1200'],
            ['2023', 'Maharashtra', 'Cotton', 'Kharif', '4200.0', '1680.0', '400'],
            ['2023', 'Uttar Pradesh', 'Sugarcane', 'Annual', '2200.0', '178200.0', '81000'],
            ['2023', 'West Bengal', 'Rice', 'Kharif', '5450.0', '15805.0', '2900'],
            ['2023', 'Gujarat', 'Groundnut', 'Kharif', '1650.0', '3960.0', '2400'],
            ['2023', 'Karnataka', 'Maize', 'Kharif', '1350.0', '4590.0', '3400'],
            ['2023', 'Andhra Pradesh', 'Rice', 'Kharif', '2400.0', '8160.0', '3400'],
            ['2023', 'Rajasthan', 'Mustard', 'Rabi', '2800.0', '4200.0', '1500'],
            ['2024', 'Punjab', 'Wheat', 'Rabi', '3510.0', '18252.0', '5200'],
            ['2024', 'Madhya Pradesh', 'Wheat', 'Rabi', '6200.0', '21080.0', '3400'],
        ],
        'title': 'National Agricultural Crop Yield and Production Statistics',
        'category': 'Agriculture',
        'source': 'Ministry of Agriculture and Farmers Welfare (Open Data Portal)',
        'description': 'Comprehensive state-level agricultural data across principal crops (Wheat, Rice, Cotton, Sugarcane) detailing land cultivation area, harvest volumes, and computed yield indices.',
        'is_public': True,
    },
    'cryptocurrency_market_cap.csv': {
        'headers': ['Rank', 'Symbol', 'Name', 'Price_USD', 'Market_Cap_Million_USD', 'Volume_24h_Million_USD', 'Change_24h_Pct'],
        'rows': [
            ['1', 'BTC', 'Bitcoin', '64250.00', '1265000', '28500', '2.45'],
            ['2', 'ETH', 'Ethereum', '3480.50', '418000', '14200', '3.12'],
            ['3', 'BNB', 'BNB', '585.20', '89500', '1100', '-0.85'],
            ['4', 'SOL', 'Solana', '145.80', '67800', '3400', '5.60'],
            ['5', 'XRP', 'XRP', '0.58', '32500', '950', '1.15'],
            ['6', 'DOGE', 'Dogecoin', '0.12', '17800', '720', '-1.40'],
            ['7', 'ADA', 'Cardano', '0.45', '16100', '410', '0.90'],
            ['8', 'AVAX', 'Avalanche', '28.40', '11200', '380', '4.25'],
            ['9', 'LINK', 'Chainlink', '14.10', '8500', '290', '2.80'],
            ['10', 'DOT', 'Polkadot', '6.85', '7900', '210', '0.50'],
        ],
        'title': 'Top 10 Cryptocurrencies Market Capitalization & Liquidity',
        'category': 'Cryptocurrency',
        'source': 'CoinGecko & CoinMarketCap Public API Snapshot',
        'description': 'Snapshot of leading cryptographic assets by valuation, highlighting 24-hour liquidity depth, price volatility percentage, and aggregate market dominance.',
        'is_public': True,
    },
    'real_estate_housing_index.csv': {
        'headers': ['Quarter', 'Metro_Area', 'Median_Sale_Price_USD', 'Inventory_Units', 'Avg_Days_On_Market', 'Mortgage_Rate_30Y_Pct'],
        'rows': [
            ['2023-Q1', 'New York Metro', '645000', '14200', '62', '6.35'],
            ['2023-Q2', 'New York Metro', '660000', '15800', '48', '6.71'],
            ['2023-Q3', 'New York Metro', '652000', '14900', '51', '7.31'],
            ['2023-Q4', 'New York Metro', '640000', '13100', '65', '7.29'],
            ['2023-Q1', 'Austin Tech Hub', '480000', '6200', '54', '6.35'],
            ['2023-Q2', 'Austin Tech Hub', '495000', '6900', '42', '6.71'],
            ['2023-Q3', 'Austin Tech Hub', '485000', '7100', '49', '7.31'],
            ['2023-Q4', 'Austin Tech Hub', '470000', '6500', '60', '7.29'],
            ['2024-Q1', 'Seattle Metro', '720000', '5800', '38', '6.82'],
            ['2024-Q2', 'Seattle Metro', '745000', '6400', '32', '6.95'],
        ],
        'title': 'Metropolitan Housing Affordability & Mortgage Rate Index',
        'category': 'Real Estate',
        'source': 'Federal Reserve Economic Data (FRED) & National Association of Realtors',
        'description': 'Quarterly residential property price trends, inventory absorption rates, and 30-year fixed mortgage rates across major metropolitan economic centers.',
        'is_public': True,
    },
    'business_gdp_indicators.csv': {
        'headers': ['Year', 'Economy_Country', 'GDP_Billion_USD', 'Annual_Growth_Pct', 'Inflation_Rate_Pct', 'Unemployment_Rate_Pct'],
        'rows': [
            ['2020', 'United States', '21060', '-2.77', '1.23', '8.05'],
            ['2021', 'United States', '23315', '5.95', '4.70', '5.35'],
            ['2022', 'United States', '25440', '2.06', '8.00', '3.65'],
            ['2023', 'United States', '27360', '2.50', '4.12', '3.62'],
            ['2020', 'India', '2670', '-5.83', '6.62', '7.86'],
            ['2021', 'India', '3150', '9.05', '5.13', '7.38'],
            ['2022', 'India', '3417', '7.24', '6.70', '7.33'],
            ['2023', 'India', '3730', '7.60', '5.40', '6.80'],
            ['2020', 'Germany', '3889', '-4.14', '0.14', '3.80'],
            ['2021', 'Germany', '4260', '3.18', '3.14', '3.58'],
            ['2022', 'Germany', '4080', '1.80', '8.67', '3.07'],
            ['2023', 'Germany', '4456', '-0.30', '5.90', '3.00'],
        ],
        'title': 'G7 and Emerging Economies Macroeconomic Growth Dynamics',
        'category': 'Business and Economics',
        'source': 'International Monetary Fund (IMF) World Economic Outlook',
        'description': 'Comparative annual macroeconomic dataset compiling gross domestic product, real GDP growth rates, headline inflation, and labor market metrics.',
        'is_public': True,
    },
    'private_research_survey.csv': {
        'headers': ['Participant_ID', 'Sector_Tracked', 'Investment_Horiz_Years', 'Risk_Tolerance', 'Expected_Return_Pct'],
        'rows': [
            ['P1001', 'Cryptocurrency', '1.5', 'High', '25.0'],
            ['P1002', 'Stock Market', '5.0', 'Moderate', '12.5'],
            ['P1003', 'Real Estate', '10.0', 'Conservative', '8.0'],
            ['P1004', 'Agriculture', '3.0', 'Moderate', '9.5'],
            ['P1005', 'Stock Market', '7.0', 'High', '16.0'],
        ],
        'title': 'Internal Thesis Survey: Investor Sentiment and Sector Allocation (Private)',
        'category': 'Other',
        'source': 'Confidential Academic Survey - Dept. of Computer Science & Economics',
        'description': 'Proprietary preliminary survey responses evaluating institutional risk tolerance and target sector yields. Kept private for active research.',
        'is_public': False,
    }
}


class Command(BaseCommand):
    help = 'Seeds the database with required categories, demo users, sample CSV files, and dataset records.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("==> Seeding Market Databank Generation & Sharing Platform data..."))

        # 1. Create Categories
        category_objects = {}
        for cat_info in CATEGORIES_DEF:
            cat, created = Category.objects.get_or_create(
                name=cat_info['name'],
                defaults={
                    'description': cat_info['description'],
                    'icon_class': cat_info['icon_class'],
                }
            )
            category_objects[cat.name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"  [+] Created Category: {cat.name}"))
            else:
                self.stdout.write(f"  [*] Existing Category: {cat.name}")

        # 2. Create Users
        admin_user, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@databank.edu',
                'first_name': 'Portal',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created_admin:
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("  [+] Created Superuser: admin (pass: Admin@123)"))

        student_user, created_student = User.objects.get_or_create(
            username='researcher',
            defaults={
                'email': 'researcher@university.edu',
                'first_name': 'Aarav',
                'last_name': 'Sharma',
            }
        )
        if created_student:
            student_user.set_password('Student@123')
            student_user.save()
            if hasattr(student_user, 'profile'):
                student_user.profile.organization = 'National Institute of Technology'
                student_user.profile.bio = 'Undergraduate research scholar focusing on empirical market data and machine learning analytics.'
                student_user.profile.save()
            self.stdout.write(self.style.SUCCESS("  [+] Created Demo User: researcher (pass: Student@123)"))

        # 3. Create Sample CSV Files on Disk and Insert Datasets
        sample_dir = os.path.join(os.getcwd(), 'sample_data')
        os.makedirs(sample_dir, exist_ok=True)

        for filename, data in SAMPLE_CSVS.items():
            csv_path = os.path.join(sample_dir, filename)
            # Write CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(data['headers'])
                writer.writerows(data['rows'])

            # Determine owner: private sample belongs to researcher, others to admin or researcher
            owner = student_user if not data['is_public'] or 'Blue-Chip' in data['title'] else admin_user

            # Check if dataset already exists
            existing_ds = Dataset.objects.filter(title=data['title']).first()
            if not existing_ds:
                category = category_objects[data['category']]
                with open(csv_path, 'rb') as f_in:
                    django_file = File(f_in, name=filename)
                    # Validate to extract metadata
                    is_valid, err, meta = validate_csv_file(django_file)
                    
                    dataset = Dataset(
                        title=data['title'],
                        description=data['description'],
                        category=category,
                        owner=owner,
                        source=data['source'],
                        is_public=data['is_public'],
                        file_size=meta.get('file_size', os.path.getsize(csv_path)),
                        row_count=meta.get('row_count', len(data['rows'])),
                        column_count=meta.get('column_count', len(data['headers'])),
                        column_names=meta.get('column_names', ', '.join(data['headers'])),
                    )
                    dataset.uploaded_file.save(filename, django_file, save=True)
                    self.stdout.write(self.style.SUCCESS(f"  [+] Created Dataset: '{dataset.title}' ({dataset.row_count} rows, {dataset.category.name})"))
            else:
                self.stdout.write(f"  [*] Existing Dataset: '{existing_ds.title}'")

        self.stdout.write(self.style.SUCCESS("\n==> Successfully populated categories, users, and sample datasets!"))
