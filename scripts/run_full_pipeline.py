"""
Script to run the complete LuggageIQ pipeline
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scraper.amazon_scraper import scrape_amazon_brands
from models.data_processor import process_scraped_data
from models.sentiment_analyzer import analyze_sentiment
from models.theme_extractor import extract_themes
from models.pricing_analyzer import analyze_pricing
from models.competitive_analyzer import analyze_competition
from models.insights_generator import generate_insights
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger('pipeline')


async def run_full_pipeline(brands: list = None, products_per_brand: int = 20):
    """Run the complete LuggageIQ pipeline"""
    
    logger.info("Starting LuggageIQ full pipeline...")
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Step 1: Scraping
    logger.info("Step 1: Scraping Amazon India...")
    if brands is None:
        brands = ['Safari', 'Skybags', 'American Tourister', 'VIP', 'Samsonite', 'Wildcraft']
    
    try:
        scrape_result = await scrape_amazon_brands(brands, products_per_brand)
        logger.info(f"Scraping completed: {scrape_result}")
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        return False
    
    # Step 2: Data Processing
    logger.info("Step 2: Processing and cleaning data...")
    try:
        products_df, reviews_df = process_scraped_data()
        logger.info(f"Data processing completed: {len(products_df)} products, {len(reviews_df)} reviews")
    except Exception as e:
        logger.error(f"Data processing failed: {str(e)}")
        return False
    
    # Step 3: Sentiment Analysis
    logger.info("Step 3: Analyzing sentiment...")
    try:
        reviews_df = analyze_sentiment(reviews_df, method='vader')
        logger.info("Sentiment analysis completed")
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        return False
    
    # Step 4: Theme Extraction
    logger.info("Step 4: Extracting themes...")
    try:
        reviews_df = extract_themes(reviews_df, method='keyword')
        logger.info("Theme extraction completed")
    except Exception as e:
        logger.error(f"Theme extraction failed: {str(e)}")
        return False
    
    # Step 5: Pricing Analysis
    logger.info("Step 5: Analyzing pricing...")
    try:
        pricing_analysis = analyze_pricing(products_df, reviews_df)
        products_df = pricing_analysis['products_with_pricing']
        logger.info("Pricing analysis completed")
    except Exception as e:
        logger.error(f"Pricing analysis failed: {str(e)}")
        return False
    
    # Step 6: Competitive Analysis
    logger.info("Step 6: Competitive analysis...")
    try:
        competitive_analysis = analyze_competition(products_df, reviews_df)
        logger.info("Competitive analysis completed")
    except Exception as e:
        logger.error(f"Competitive analysis failed: {str(e)}")
        return False
    
    # Step 7: Insights Generation
    logger.info("Step 7: Generating insights...")
    try:
        insights = generate_insights(products_df, reviews_df, competitive_analysis)
        logger.info(f"Generated {len(insights)} insights")
    except Exception as e:
        logger.error(f"Insights generation failed: {str(e)}")
        return False
    
    # Save final processed data
    logger.info("Saving final processed data...")
    try:
        products_df.to_csv(f"{Config.PROCESSED_DATA_PATH}/products_final.csv", index=False)
        reviews_df.to_csv(f"{Config.PROCESSED_DATA_PATH}/reviews_final.csv", index=False)
        logger.info("Final data saved")
    except Exception as e:
        logger.error(f"Failed to save final data: {str(e)}")
        return False
    
    logger.info("LuggageIQ pipeline completed successfully!")
    return True


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run LuggageIQ full pipeline')
    parser.add_argument('--brands', nargs='+', help='Brands to scrape')
    parser.add_argument('--products-per-brand', type=int, default=20, help='Products per brand')
    
    args = parser.parse_args()
    
    # Run pipeline
    success = asyncio.run(run_full_pipeline(args.brands, args.products_per_brand))
    
    if success:
        print("\n" + "="*50)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("Data is ready for dashboard and API usage.")
        print("Start the API: python api/main.py")
        print("Start the dashboard: streamlit run dashboard/app.py")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("PIPELINE FAILED!")
        print("="*50)
        sys.exit(1)


if __name__ == "__main__":
    main()
