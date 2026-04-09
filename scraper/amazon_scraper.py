"""
Enhanced Amazon India scraper for LuggageIQ products with pagination support
"""

import asyncio
import time
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, quote
import pandas as pd
import random

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from utils.config import Config
from utils.logger import setup_logger
from utils.data_utils import save_data, clean_text, extract_price, extract_rating

logger = setup_logger('scraper')


class AmazonScraper:
    """Enhanced Amazon India product and review scraper with pagination support"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.products_data = []
        self.reviews_data = []
        self.scraped_urls = set()  # Track scraped URLs to avoid duplicates
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Initialize browser and page"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent=Config.USER_AGENT,
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = await self.context.new_page()
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser closed")
    
    async def navigate_to_search(self, query: str) -> bool:
        """Navigate to Amazon India search results"""
        try:
            search_url = f"{Config.AMAZON_SEARCH_URL}?k={quote(query)}&ref=sr_pg_1"
            logger.info(f"Navigating to: {search_url}")
            
            await self.page.goto(search_url, wait_until='domcontentloaded')
            await self.page.wait_for_timeout(2000)
            
            # Check if we got search results
            await self.page.wait_for_selector('.s-result-list', timeout=10000)
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to search: {str(e)}")
            return False
    
    async def extract_search_results(self, max_pages: int = 3) -> List[Dict]:
        """Extract product information from multiple search results pages with pagination"""
        products = []
        current_page = 1
        
        while current_page <= max_pages:
            try:
                logger.info(f"Extracting products from page {current_page}")
                
                # Scroll to load more results
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(2000)
                
                # Get all product containers
                product_elements = await self.page.query_selector_all('[data-component-type="s-search-result"]')
                logger.info(f"Found {len(product_elements)} products on page {current_page}")
                
                page_products = []
                for element in product_elements:
                    try:
                        product = await self._extract_product_from_element(element)
                        if product:
                            products.append(product)
                    except Exception as e:
                        logger.warning(f"Failed to extract product: {str(e)}")
                        continue
                
                # Check if we can go to next page
                next_button = await self.page.query_selector('.s-pagination-next:not(.a-disabled)')
                if not next_button or current_page >= max_pages:
                    break
                
                # Click next page
                await next_button.click()
                await self.page.wait_for_timeout(3000)
                current_page += 1
                
            except Exception as e:
                logger.error(f"Error processing page {current_page}: {str(e)}")
                break
        
        return products
    
    async def _extract_product_from_element(self, element) -> Optional[Dict]:
        """Extract product details from a single search result element"""
        try:
            # Product title
            title_element = await element.query_selector('h2 a span')
            title = await title_element.inner_text() if title_element else ""
            
            # Product URL
            link_element = await element.query_selector('h2 a')
            product_url = await link_element.get_attribute('href') if link_element else ""
            if product_url:
                product_url = urljoin(Config.AMAZON_BASE_URL, product_url)
            
            # Brand name (extract from title or brand element)
            brand = self._extract_brand_from_title(title)
            brand_element = await element.query_selector('.a-size-base-plus')
            if brand_element:
                brand_text = await brand_element.inner_text()
                brand = brand_text.strip()
            
            # Price
            price_element = await element.query_selector('.a-price-whole')
            price_text = await price_element.inner_text() if price_element else ""
            price = extract_price(price_text)
            
            # MRP (if available)
            mrp_element = await element.query_selector('.a-price.a-text-price .a-offscreen')
            mrp_text = await mrp_element.inner_text() if mrp_element else ""
            mrp = extract_price(mrp_text)
            
            # Discount percentage
            discount_element = await element.query_selector('.a-color-price')
            discount_text = await discount_element.inner_text() if discount_element else ""
            discount_pct = self._extract_discount_percentage(discount_text)
            
            # Rating
            rating_element = await element.query_selector('i.a-icon-alt')
            rating_text = await rating_element.inner_text() if rating_element else ""
            rating = extract_rating(rating_text)
            
            # Review count
            review_count_element = await element.query_selector('a.a-link-normal span')
            review_count_text = await review_count_element.inner_text() if review_count_element else ""
            review_count = self._extract_review_count(review_count_text)
            
            # Generate product ID
            product_id = f"{brand}_{title[:50].replace(' ', '_')}".lower()
            
            product_data = {
                'product_id': product_id,
                'title': clean_text(title),
                'brand': clean_text(brand),
                'price': price,
                'mrp': mrp,
                'discount_pct': discount_pct,
                'rating': rating,
                'review_count': review_count,
                'product_url': product_url,
                'scraped_at': pd.Timestamp.now().isoformat()
            }
            
            return product_data
            
        except Exception as e:
            logger.warning(f"Error extracting product element: {str(e)}")
            return None
    
    def _extract_brand_from_title(self, title: str) -> str:
        """Extract brand name from product title"""
        if not title:
            return ""
        
        # Common luggage brands
        brands = [
            'Safari', 'Skybags', 'American Tourister', 'VIP', 'Samsonite',
            'Wildcraft', 'Aristocrat', 'Delsey', 'Tumi', 'Briggs & Riley',
            'Travel Blue', 'Ace', 'Swissgear', 'Olympia', 'Heys'
        ]
        
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        
        # If no known brand found, return first word
        return title.split()[0] if title else ""
    
    def _extract_discount_percentage(self, discount_text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        if not discount_text:
            return None
        
        import re
        match = re.search(r'(\d+)%', discount_text)
        if match:
            return float(match.group(1))
        return None
    
    def _extract_review_count(self, review_text: str) -> Optional[int]:
        """Extract review count from text"""
        if not review_text:
            return None
        
        import re
        # Remove commas and extract number
        match = re.search(r'([\d,]+)', review_text.replace(',', ''))
        if match:
            return int(match.group(1))
        return None
    
    async def extract_product_reviews(self, product_url: str, product_id: str, max_reviews: int = None) -> List[Dict]:
        """Extract reviews from a product page with enhanced pagination"""
        if max_reviews is None:
            max_reviews = 50  # Increased from default to collect more reviews
        
        reviews = []
        try:
            logger.info(f"Extracting up to {max_reviews} reviews for product: {product_id}")
            
            await self.page.goto(product_url, wait_until='domcontentloaded')
            await self.page.wait_for_timeout(2000)
            
            # Click on "See all reviews" if available
            try:
                see_all_button = await self.page.query_selector('[data-hook="see-all-reviews-link-foot"]')
                if see_all_button:
                    await see_all_button.click()
                    await self.page.wait_for_timeout(3000)
            except Exception:
                logger.debug("No 'See all reviews' button found")
            
            # Extract reviews with pagination
            current_reviews_count = 0
            page_num = 1
            max_pages = 10  # Limit pages to avoid infinite loops
            
            while current_reviews_count < max_reviews and page_num <= max_pages:
                try:
                    # Scroll to load reviews
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await self.page.wait_for_timeout(2000)
                    
                    # Get review elements
                    review_elements = await self.page.query_selector_all('[data-hook="review"]')
                    logger.info(f"Found {len(review_elements)} reviews on page {page_num}")
                    
                    for element in review_elements:
                        if current_reviews_count >= max_reviews:
                            break
                        
                        try:
                            review = await self._extract_review_from_element(element, product_id)
                            if review:
                                reviews.append(review)
                                current_reviews_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to extract review: {str(e)}")
                            continue
                    
                    # Check if we can go to next page
                    if current_reviews_count >= max_reviews:
                        break
                    
                    next_button = await self.page.query_selector('.a-pagination .a-next:not(.a-disabled)')
                    if not next_button:
                        break
                    
                    # Click next page
                    await next_button.click()
                    await self.page.wait_for_timeout(3000)
                    page_num += 1
                    
                except Exception as e:
                    logger.error(f"Error processing review page {page_num}: {str(e)}")
                    break
            
            logger.info(f"Extracted {len(reviews)} reviews for product {product_id}")
            
        except Exception as e:
            logger.error(f"Failed to extract reviews for {product_id}: {str(e)}")
        
        return reviews
    
    async def _extract_review_from_element(self, element, product_id: str) -> Optional[Dict]:
        """Extract review details from a review element"""
        try:
            # Review rating
            rating_element = await element.query_selector('[data-hook="review-star-rating"] span')
            rating_text = await rating_element.inner_text() if rating_element else ""
            rating = extract_rating(rating_text)
            
            # Review title
            title_element = await element.query_selector('[data-hook="review-title"] span')
            title = await title_element.inner_text() if title_element else ""
            
            # Review body
            body_element = await element.query_selector('[data-hook="review-body"] span')
            body = await body_element.inner_text() if body_element else ""
            
            # Review date
            date_element = await element.query_selector('[data-hook="review-date"]')
            date_text = await date_element.inner_text() if date_element else ""
            
            # Generate review ID
            review_id = f"{product_id}_{len(self.reviews_data)}"
            
            review_data = {
                'review_id': review_id,
                'product_id': product_id,
                'rating': rating,
                'title': clean_text(title),
                'text': clean_text(body),
                'date': date_text,
                'scraped_at': pd.Timestamp.now().isoformat()
            }
            
            return review_data
            
        except Exception as e:
            logger.warning(f"Error extracting review: {str(e)}")
            return None
    
    async def scrape_brands(self, brands: List[str], products_per_brand: int = 20) -> Dict:
        """Scrape products and reviews for given brands"""
        logger.info(f"Starting scrape for brands: {brands}")
        
        all_products = []
        all_reviews = []
        
        for brand in brands:
            try:
                logger.info(f"Scraping brand: {brand}")
                
                # Search for brand products
                search_query = f"{brand} luggage"
                success = await self.navigate_to_search(search_query)
                
                if not success:
                    logger.warning(f"Failed to search for {brand}")
                    continue
                
                # Extract products from search results
                products = await self.extract_search_results()
                
                # Limit products per brand
                products = products[:products_per_brand]
                
                # Extract reviews for each product
                for product in products:
                    try:
                        reviews = await self.extract_product_reviews(
                            product['product_url'], 
                            product['product_id']
                        )
                        all_reviews.extend(reviews)
                        
                        # Add delay between products
                        await asyncio.sleep(Config.SCRAPING_DELAY)
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract reviews for {product['product_id']}: {str(e)}")
                        continue
                
                all_products.extend(products)
                
                # Add delay between brands
                await asyncio.sleep(Config.SCRAPING_DELAY * 2)
                
            except Exception as e:
                logger.error(f"Failed to scrape brand {brand}: {str(e)}")
                continue
        
        # Save data
        products_df = pd.DataFrame(all_products)
        reviews_df = pd.DataFrame(all_reviews)
        
        Config.ensure_directories()
        save_data(products_df, f"{Config.RAW_DATA_PATH}/products.csv")
        save_data(reviews_df, f"{Config.RAW_DATA_PATH}/reviews.csv")
        
        result = {
            'products_count': len(all_products),
            'reviews_count': len(all_reviews),
            'brands_scraped': brands,
            'products_file': f"{Config.RAW_DATA_PATH}/products.csv",
            'reviews_file': f"{Config.RAW_DATA_PATH}/reviews.csv"
        }
        
        logger.info(f"Scraping completed: {result}")
        return result


# Convenience function for synchronous usage
async def scrape_amazon_brands(brands: List[str], products_per_brand: int = 20) -> Dict:
    """Convenience function to scrape Amazon brands"""
    async with AmazonScraper() as scraper:
        return await scraper.scrape_brands(brands, products_per_brand)
