"""
Create sample data for testing LuggageIQ without scraping
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def create_sample_products():
    """Create sample product data"""
    brands = ['Safari', 'Skybags', 'American Tourister', 'VIP', 'Samsonite', 'Wildcraft']
    product_types = ['Trolley Bag', 'Backpack', 'Duffle Bag', 'Suitcase', 'Cabin Luggage', 'Check-in Luggage']
    
    products = []
    product_id = 1
    
    for brand in brands:
        for _ in range(random.randint(3, 7)):  # 3-7 products per brand
            product_type = random.choice(product_types)
            price = random.randint(800, 8000)
            mrp = int(price * random.uniform(1.1, 1.4))
            discount_pct = round(((mrp - price) / mrp) * 100, 1)
            rating = round(random.uniform(3.0, 5.0), 1)
            review_count = random.randint(10, 500)
            
            products.append({
                'product_id': f'p{product_id}',
                'title': f'{brand} {product_type} {product_id}',
                'brand': brand,
                'price': price,
                'mrp': mrp,
                'discount_pct': discount_pct,
                'rating': rating,
                'review_count': review_count,
                'product_url': f'https://amazon.in/dp/{product_id}',
                'scraped_at': datetime.now().isoformat()
            })
            product_id += 1
    
    return pd.DataFrame(products)

def create_sample_reviews(products_df):
    """Create sample review data"""
    review_templates = {
        'positive': [
            'Excellent quality, very durable and spacious',
            'Great value for money, wheels are smooth',
            'Perfect size for cabin luggage, lightweight',
            'Amazing build quality, worth every penny',
            'Highly recommended, best purchase ever'
        ],
        'negative': [
            'Zipper broke after 2 trips, poor quality',
            'Too expensive for the quality offered',
            'Wheels are wobbly, not stable',
            'Material feels cheap, disappointed',
            'Handle broke after first use'
        ],
        'neutral': [
            'Average product, nothing special',
            'Decent quality for the price',
            'Okay for occasional use',
            'Meets expectations but not exceptional',
            'Standard product, no complaints'
        ]
    }
    
    themes = {
        'wheels': ['wheel', 'wheels', 'rolling', 'spinner'],
        'handle': ['handle', 'grip', 'telescopic'],
        'zipper': ['zipper', 'zip', 'closure'],
        'durability': ['durable', 'quality', 'build'],
        'space': ['space', 'capacity', 'room'],
        'material': ['material', 'fabric', 'texture']
    }
    
    reviews = []
    review_id = 1
    
    for _, product in products_df.iterrows():
        num_reviews = random.randint(3, 10)
        
        for _ in range(num_reviews):
            # Choose sentiment based on product rating
            if product['rating'] >= 4.0:
                sentiment_weights = [0.7, 0.1, 0.2]  # positive, negative, neutral
            elif product['rating'] <= 3.0:
                sentiment_weights = [0.1, 0.6, 0.3]
            else:
                sentiment_weights = [0.3, 0.2, 0.5]
            
            sentiment = random.choices(['positive', 'negative', 'neutral'], weights=sentiment_weights)[0]
            
            # Generate review text
            template = random.choice(review_templates[sentiment])
            
            # Add theme keywords
            theme_keywords = []
            if 'wheel' in template.lower():
                theme_keywords.append('wheels')
            if 'handle' in template.lower():
                theme_keywords.append('handle')
            if 'zipper' in template.lower():
                theme_keywords.append('zipper')
            if 'quality' in template.lower() or 'durable' in template.lower():
                theme_keywords.append('durability')
            if 'space' in template.lower() or 'capacity' in template.lower():
                theme_keywords.append('space')
            if 'material' in template.lower():
                theme_keywords.append('material')
            
            # Generate rating based on sentiment
            if sentiment == 'positive':
                rating = random.randint(4, 5)
            elif sentiment == 'negative':
                rating = random.randint(1, 2)
            else:
                rating = random.randint(3, 4)
            
            # Generate date (within last 6 months)
            days_ago = random.randint(0, 180)
            review_date = (datetime.now() - timedelta(days=days_ago)).strftime('%d %B %Y')
            
            reviews.append({
                'review_id': f'r{review_id}',
                'product_id': product['product_id'],
                'rating': rating,
                'title': f'{sentiment.title()} review',
                'text': template,
                'date': review_date,
                'scraped_at': datetime.now().isoformat(),
                'themes': theme_keywords
            })
            review_id += 1
    
    return pd.DataFrame(reviews)

def main():
    """Create and save sample data"""
    print("Creating sample data for LuggageIQ...")
    
    # Create sample products
    products_df = create_sample_products()
    print(f"Created {len(products_df)} sample products")
    
    # Create sample reviews
    reviews_df = create_sample_reviews(products_df)
    print(f"Created {len(reviews_df)} sample reviews")
    
    # Save data
    import os
    os.makedirs("data/raw", exist_ok=True)
    
    # Save raw data
    products_df.to_csv("data/raw/products.csv", index=False)
    reviews_df.to_csv("data/raw/reviews.csv", index=False)
    
    print("Sample data saved to data/raw/")
    print("\nData Summary:")
    print(f"Brands: {products_df['brand'].nunique()}")
    print(f"Products per brand: {products_df.groupby('brand').size().to_dict()}")
    print(f"Average rating: {products_df['rating'].mean():.2f}")
    print(f"Average price: ${products_df['price'].mean():.2f}")
    print(f"Total reviews: {len(reviews_df)}")
    print(f"Reviews per product: {len(reviews_df) / len(products_df):.1f}")

if __name__ == "__main__":
    main()
