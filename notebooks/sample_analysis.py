"""
Sample analysis notebook for LuggageIQ
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from models.data_processor import DataProcessor
from models.sentiment_analyzer import SentimentAnalyzer
from models.theme_extractor import ThemeExtractor
from models.pricing_analyzer import PricingAnalyzer
from models.competitive_analyzer import CompetitiveAnalyzer
from models.insights_generator import InsightsGenerator
from utils.config import Config

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def create_sample_data():
    """Create sample data for demonstration"""
    # Sample products
    products_data = {
        'product_id': [f'p{i}' for i in range(1, 21)],
        'title': [
            'Safari Polycarbonate Luggage Set 3 Pieces',
            'Skybags Strolly Bag 28 inch',
            'American Tourister Suitcase 24 inch',
            'VIP Backpack Laptop Bag',
            'Samsonite Spinner 29 inch',
            'Wildcraft Rucksack 40L',
            'Safari Duffle Bag',
            'Skybags Cabin Luggage',
            'American Tourister Backpack',
            'VIP Trolley Bag',
            'Samsonite Laptop Bag',
            'Wildcraft Travel Bag',
            'Safari Hand Luggage',
            'Skybags Check-in Luggage',
            'American Tourister Trolley',
            'VIP Suitcase',
            'Samsonite Cabin Bag',
            'Wildcraft Backpack',
            'Safari Travel Pack',
            'Skybags Premium Luggage'
        ],
        'brand': [
            'Safari', 'Skybags', 'American Tourister', 'VIP', 'Samsonite',
            'Wildcraft', 'Safari', 'Skybags', 'American Tourister', 'VIP',
            'Samsonite', 'Wildcraft', 'Safari', 'Skybags', 'American Tourister',
            'VIP', 'Samsonite', 'Wildcraft', 'Safari', 'Skybags'
        ],
        'price': [
            3500, 2800, 4200, 1500, 8500, 2200, 1800, 3200, 1200, 3800,
            2800, 2500, 2900, 4500, 3900, 3200, 4800, 1800, 2400, 5200
        ],
        'mrp': [
            4500, 3500, 5200, 1800, 9500, 2800, 2200, 4000, 1500, 4500,
            3500, 3000, 3500, 5500, 4800, 4000, 5800, 2200, 3000, 6200
        ],
        'rating': [
            4.2, 3.8, 4.5, 3.5, 4.7, 4.0, 3.9, 4.1, 3.6, 4.3,
            4.6, 3.7, 4.0, 3.9, 4.4, 3.8, 4.5, 4.1, 3.9, 4.2
        ],
        'review_count': [
            234, 156, 412, 89, 523, 178, 145, 267, 98, 345,
            412, 134, 189, 278, 356, 223, 467, 167, 198, 289
        ]
    }
    
    # Sample reviews
    reviews_data = []
    review_texts = [
        "Excellent quality, very durable and spacious",
        "Good value for money, wheels are smooth",
        "Zipper broke after 2 trips, poor quality",
        "Great design, handles are comfortable",
        "Material is good but scratches easily",
        "Perfect size for cabin luggage",
        "Too expensive for the quality offered",
        "Best purchase ever, highly recommended",
        "Average product, nothing special",
        "Lightweight and easy to carry"
    ]
    
    for i, product_id in enumerate(products_data['product_id']):
        for j in range(5):  # 5 reviews per product
            review_text = review_texts[j % len(review_texts)]
            rating = np.random.randint(1, 6)
            
            reviews_data.append({
                'review_id': f'r{len(reviews_data) + 1}',
                'product_id': product_id,
                'rating': rating,
                'title': f'Review {j+1}',
                'text': review_text
            })
    
    products_df = pd.DataFrame(products_data)
    reviews_df = pd.DataFrame(reviews_data)
    
    return products_df, reviews_df

def run_sample_analysis():
    """Run complete sample analysis"""
    print("Creating sample data...")
    products_df, reviews_df = create_sample_data()
    
    print(f"Created {len(products_df)} products and {len(reviews_df)} reviews")
    
    # Data processing
    print("\n1. Processing data...")
    processor = DataProcessor()
    processor.products_df = products_df
    processor.reviews_df = reviews_df
    
    clean_products = processor.clean_products_data()
    clean_reviews = processor.clean_reviews_data()
    
    print(f"Processed {len(clean_products)} products and {len(clean_reviews)} reviews")
    
    # Sentiment analysis
    print("\n2. Analyzing sentiment...")
    analyzer = SentimentAnalyzer()
    analyzed_reviews = analyzer.analyze_dataframe(clean_reviews)
    
    sentiment_summary = analyzer.get_sentiment_summary(analyzed_reviews)
    print(f"Average sentiment: {sentiment_summary['average_scores']['avg_sentiment']:.2f}")
    
    # Theme extraction
    print("\n3. Extracting themes...")
    extractor = ThemeExtractor()
    reviews_with_themes = extractor.extract_themes_from_dataframe(analyzed_reviews)
    
    theme_summary = extractor.get_theme_summary(reviews_with_themes)
    print(f"Top themes: {list(theme_summary['theme_counts'].keys())[:3]}")
    
    # Pricing analysis
    print("\n4. Analyzing pricing...")
    pricing_analyzer = PricingAnalyzer()
    products_with_pricing = pricing_analyzer.analyze_pricing(clean_products)
    
    brand_pricing = pricing_analyzer.get_brand_pricing_summary(products_with_pricing)
    print(f"Average price by brand: {brand_pricing[['brand', 'avg_price']].to_dict('records')}")
    
    # Competitive analysis
    print("\n5. Competitive analysis...")
    competitive_analyzer = CompetitiveAnalyzer()
    competitive_analysis = competitive_analyzer.analyze_competitive_landscape(
        products_with_pricing, reviews_with_themes
    )
    
    print("Top brands by competitive score:")
    competitive_scores = competitive_analysis['competitive_scores']
    for _, row in competitive_scores.head(3).iterrows():
        print(f"  {row['brand']}: {row['competitive_score']:.1f}")
    
    # Insights generation
    print("\n6. Generating insights...")
    insights_generator = InsightsGenerator()
    insights = insights_generator.generate_insights(
        products_with_pricing, reviews_with_themes, competitive_analysis
    )
    
    print(f"Generated {len(insights)} insights:")
    for insight in insights[:3]:
        print(f"  - {insight['title']}")
    
    # Visualizations
    print("\n7. Creating visualizations...")
    
    # Price distribution
    plt.figure(figsize=(10, 6))
    plt.subplot(2, 2, 1)
    plt.hist(products_with_pricing['price'], bins=10, alpha=0.7)
    plt.title('Price Distribution')
    plt.xlabel('Price ($)')
    plt.ylabel('Frequency')
    
    # Rating distribution
    plt.subplot(2, 2, 2)
    plt.hist(products_with_pricing['rating'], bins=5, alpha=0.7)
    plt.title('Rating Distribution')
    plt.xlabel('Rating')
    plt.ylabel('Frequency')
    
    # Brand comparison
    plt.subplot(2, 2, 3)
    brand_counts = products_with_pricing['brand'].value_counts()
    plt.bar(brand_counts.index, brand_counts.values)
    plt.title('Products by Brand')
    plt.xlabel('Brand')
    plt.ylabel('Number of Products')
    plt.xticks(rotation=45)
    
    # Sentiment distribution
    plt.subplot(2, 2, 4)
    sentiment_counts = reviews_with_themes['sentiment_label'].value_counts()
    plt.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%')
    plt.title('Sentiment Distribution')
    
    plt.tight_layout()
    plt.savefig('notebooks/sample_analysis.png')
    plt.show()
    
    print("\nAnalysis completed! Check 'sample_analysis.png' for visualizations.")
    
    return {
        'products': products_with_pricing,
        'reviews': reviews_with_themes,
        'competitive_analysis': competitive_analysis,
        'insights': insights
    }

if __name__ == "__main__":
    results = run_sample_analysis()
