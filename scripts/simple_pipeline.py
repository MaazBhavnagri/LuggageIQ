"""
Simple pipeline for LuggageIQ - focus on getting API and dashboard working
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from models.data_processor import DataProcessor
from models.sentiment_analyzer import SentimentAnalyzer
from models.theme_extractor import ThemeExtractor
from models.pricing_analyzer import PricingAnalyzer

def main():
    """Run simple pipeline for API and dashboard"""
    print("Running simple LuggageIQ pipeline...")
    
    # Load scraped Amazon India dataset
    try:
        products_df = pd.read_csv("data/raw/products.csv")
        reviews_df = pd.read_csv("data/raw/reviews.csv")
        print(f"Loaded {len(products_df)} products and {len(reviews_df)} reviews")
    except Exception as e:
        print(f"Error loading scraped dataset: {e}")
        return False
    
    # Step 1: Data Processing
    print("\n1. Processing data...")
    try:
        processor = DataProcessor()
        processor.products_df = products_df
        processor.reviews_df = reviews_df
        
        clean_products = processor.clean_products_data()
        clean_reviews = processor.clean_reviews_data()
        
        print(f"   Processed {len(clean_products)} products and {len(clean_reviews)} reviews")
    except Exception as e:
        print(f"   Error in data processing: {e}")
        return False
    
    # Step 2: Sentiment Analysis
    print("\n2. Analyzing sentiment...")
    try:
        analyzer = SentimentAnalyzer(method='vader')
        reviews_with_sentiment = analyzer.analyze_dataframe(clean_reviews)
        print(f"   Analyzed sentiment for {len(reviews_with_sentiment)} reviews")
    except Exception as e:
        print(f"   Error in sentiment analysis: {e}")
        return False
    
    # Step 3: Theme Extraction
    print("\n3. Extracting themes...")
    try:
        extractor = ThemeExtractor(method='keyword')
        reviews_with_themes = extractor.extract_themes_from_dataframe(reviews_with_sentiment)
        print(f"   Extracted themes from {len(reviews_with_themes)} reviews")
    except Exception as e:
        print(f"   Error in theme extraction: {e}")
        return False
    
    # Step 4: Pricing Analysis
    print("\n4. Analyzing pricing...")
    try:
        pricing_analyzer = PricingAnalyzer()
        products_with_pricing = pricing_analyzer.analyze_pricing(clean_products)
        print(f"   Analyzed pricing for {len(products_with_pricing)} products")
    except Exception as e:
        print(f"   Error in pricing analysis: {e}")
        return False
    
    # Save processed data
    print("\n5. Saving processed data...")
    try:
        os.makedirs("data/processed", exist_ok=True)
        
        products_with_pricing.to_csv("data/processed/products_clean.csv", index=False)
        reviews_with_themes.to_csv("data/processed/reviews_clean.csv", index=False)
        
        print("   Processed data saved to data/processed/")
    except Exception as e:
        print(f"   Error saving data: {e}")
        return False
    
    print("\n" + "="*50)
    print("SIMPLE PIPELINE COMPLETED!")
    print("="*50)
    print("Data is ready for API and dashboard.")
    print("\nNext steps:")
    print("1. Start the API: python api/main.py")
    print("2. Start the dashboard: streamlit run dashboard/app.py")
    print("="*50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
