"""
Process scraped Amazon India dataset for LuggageIQ - run full analysis pipeline
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
from models.competitive_analyzer import CompetitiveAnalyzer
from models.insights_generator import InsightsGenerator

def main():
    """Process scraped Amazon India dataset through full pipeline"""
    print("Processing scraped Amazon India dataset through LuggageIQ pipeline...")
    
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
        
        sentiment_summary = analyzer.get_sentiment_summary(reviews_with_sentiment)
        avg_sentiment = sentiment_summary.get('average_scores', {}).get('avg_sentiment', 0)
        print(f"   Average sentiment: {avg_sentiment:.2f}")
    except Exception as e:
        print(f"   Error in sentiment analysis: {e}")
        return False
    
    # Step 3: Theme Extraction
    print("\n3. Extracting themes...")
    try:
        extractor = ThemeExtractor(method='keyword')
        reviews_with_themes = extractor.extract_themes_from_dataframe(reviews_with_sentiment)
        
        theme_summary = extractor.get_theme_summary(reviews_with_themes)
        top_themes = list(theme_summary['theme_counts'].keys())[:3]
        print(f"   Top themes: {', '.join(top_themes)}")
    except Exception as e:
        print(f"   Error in theme extraction: {e}")
        return False
    
    # Step 4: Pricing Analysis
    print("\n4. Analyzing pricing...")
    try:
        pricing_analyzer = PricingAnalyzer()
        products_with_pricing = pricing_analyzer.analyze_pricing(clean_products)
        products_with_pricing = pricing_analyzer.calculate_value_scores(products_with_pricing, reviews_with_themes)
        
        brand_pricing = pricing_analyzer.get_brand_pricing_summary(products_with_pricing)
        print(f"   Analyzed pricing for {len(brand_pricing)} brands")
    except Exception as e:
        print(f"   Error in pricing analysis: {e}")
        return False
    
    # Step 5: Competitive Analysis
    print("\n5. Running competitive analysis...")
    try:
        competitive_analyzer = CompetitiveAnalyzer()
        
        # Ensure data has required columns
        if 'sentiment_score' not in reviews_with_themes.columns:
            print("   Missing sentiment_score in reviews, skipping competitive analysis")
            competitive_analysis = None
        else:
            competitive_analysis = competitive_analyzer.analyze_competitive_landscape(
                products_with_pricing, reviews_with_themes
            )
            
            competitive_scores = competitive_analysis['competitive_scores']
            print(f"   Competitive analysis completed")
            print(f"   Top brand: {competitive_scores.iloc[0]['brand']}")
    except Exception as e:
        print(f"   Error in competitive analysis: {e}")
        print("   Continuing without competitive analysis...")
        competitive_analysis = None
    
    # Step 6: Insights Generation
    print("\n6. Generating insights...")
    try:
        insights_generator = InsightsGenerator()
        insights = insights_generator.generate_insights(
            products_with_pricing, reviews_with_themes, competitive_analysis
        )
        
        print(f"   Generated {len(insights)} insights")
        for insight in insights[:3]:
            print(f"   - {insight['title']}")
    except Exception as e:
        print(f"   Error in insights generation: {e}")
        return False
    
    # Save processed data
    print("\n7. Saving processed data...")
    try:
        os.makedirs("data/processed", exist_ok=True)
        
        products_with_pricing.to_csv("data/processed/products_clean.csv", index=False)
        reviews_with_themes.to_csv("data/processed/reviews_clean.csv", index=False)
        
        print("   Processed data saved to data/processed/")
    except Exception as e:
        print(f"   Error saving data: {e}")
        return False
    
    print("\n" + "="*50)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("Data is ready for dashboard and API usage.")
    print("\nNext steps:")
    print("1. Start the API: python api/main.py")
    print("2. Start the dashboard: streamlit run dashboard/app.py")
    print("="*50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
