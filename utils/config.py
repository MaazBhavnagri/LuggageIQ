"""
Configuration management for LuggageIQ
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for LuggageIQ application"""
    
    # Scraping Configuration
    SCRAPING_DELAY: int = int(os.getenv('SCRAPING_DELAY', 2))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', 3))
    REVIEW_COUNT_PER_PRODUCT: int = int(os.getenv('REVIEW_COUNT_PER_PRODUCT', 50))
    USER_AGENT: str = os.getenv('USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # API Configuration
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', 8000))
    
    # Dashboard Configuration
    DASHBOARD_PORT: int = int(os.getenv('DASHBOARD_PORT', 8501))
    
    # Data Paths
    DATA_PATH: str = os.getenv('DATA_PATH', './data')
    RAW_DATA_PATH: str = os.getenv('RAW_DATA_PATH', './data/raw')
    PROCESSED_DATA_PATH: str = os.getenv('PROCESSED_DATA_PATH', './data/processed')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', './logs/luggageiq.log')
    
    # Amazon India Configuration
    AMAZON_BASE_URL: str = 'https://www.amazon.in'
    AMAZON_SEARCH_URL: str = 'https://www.amazon.in/s'
    
    # Sentiment Analysis Configuration
    SENTIMENT_THRESHOLD_POSITIVE: float = 0.1
    SENTIMENT_THRESHOLD_NEGATIVE: float = -0.1
    
    # Theme Extraction Keywords
    THEME_KEYWORDS = {
        'wheels': ['wheel', 'wheels', 'rolling', 'caster', 'casters', 'spinner'],
        'handle': ['handle', 'handles', 'grip', 'telescopic', 'retractable'],
        'zipper': ['zipper', 'zip', 'zipping', 'closure', 'lock'],
        'durability': ['durable', 'sturdy', 'strong', 'break', 'broken', 'damage', 'quality'],
        'space': ['space', 'capacity', 'room', 'size', 'fit', 'compact', 'spacious'],
        'material': ['material', 'fabric', 'polycarbonate', 'hard', 'soft', 'texture']
    }
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_PATH,
            cls.RAW_DATA_PATH,
            cls.PROCESSED_DATA_PATH,
            './logs'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def get_amazon_search_url(cls, query: str) -> str:
        """Generate Amazon India search URL"""
        return f"{cls.AMAZON_SEARCH_URL}?k={query.replace(' ', '+')}&ref=sr_pg_1"
