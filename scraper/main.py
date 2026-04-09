"""
Main entry point for the scraper module
"""

import asyncio
import sys
from typing import List

from scraper.amazon_scraper import scrape_amazon_brands
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger('scraper_main')


async def main():
    """Main function to run the scraper"""
    
    # Default luggage brands to scrape
    default_brands = [
        'Safari',
        'Skybags', 
        'American Tourister',
        'VIP',
        'Samsonite',
        'Wildcraft'
    ]
    
    # Get brands from command line arguments or use defaults
    brands = sys.argv[1:] if len(sys.argv) > 1 else default_brands
    products_per_brand = 60  # Increased to collect more products per brand
    
    logger.info(f"Starting scraper for brands: {brands}")
    
    try:
        # Ensure directories exist
        Config.ensure_directories()
        
        # Run scraper
        result = await scrape_amazon_brands(brands, products_per_brand)
        
        logger.info("Scraping completed successfully!")
        logger.info(f"Products scraped: {result['products_count']}")
        logger.info(f"Reviews scraped: {result['reviews_count']}")
        logger.info(f"Data saved to: {result['products_file']}")
        logger.info(f"Reviews saved to: {result['reviews_file']}")
        
        print("\n" + "="*50)
        print("SCRAPING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Brands scraped: {', '.join(result['brands_scraped'])}")
        print(f"Total products: {result['products_count']}")
        print(f"Total reviews: {result['reviews_count']}")
        print(f"Products file: {result['products_file']}")
        print(f"Reviews file: {result['reviews_file']}")
        print("="*50)
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        print(f"\nERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
