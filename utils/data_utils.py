"""
Data utilities for LuggageIQ
"""

import pandas as pd
import re
from typing import Dict, List, Optional, Union
import os

from .config import Config


def load_data(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load data from CSV file
    
    Args:
        filepath: Path to CSV file
        **kwargs: Additional arguments for pd.read_csv
    
    Returns:
        Loaded DataFrame
    """
    try:
        return pd.read_csv(filepath, **kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(f"Data file not found: {filepath}")
    except Exception as e:
        raise Exception(f"Error loading data from {filepath}: {str(e)}")


def save_data(df: pd.DataFrame, filepath: str, **kwargs) -> None:
    """
    Save DataFrame to CSV file
    
    Args:
        df: DataFrame to save
        filepath: Path to save CSV file
        **kwargs: Additional arguments for df.to_csv
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, **kwargs)


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    if pd.isna(text) or text is None:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', str(text).strip())
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()


def extract_price(price_text: str) -> Optional[float]:
    """
    Extract numeric price from text
    
    Args:
        price_text: Text containing price
    
    Returns:
        Extracted price as float or None
    """
    if pd.isna(price_text) or price_text is None:
        return None
    
    # Extract numbers with optional commas and decimals
    price_match = re.search(r'[\d,]+\.?\d*', str(price_text).replace('?', ''))
    if price_match:
        price_str = price_match.group().replace(',', '')
        try:
            return float(price_str)
        except ValueError:
            return None
    
    return None


def extract_rating(rating_text: str) -> Optional[float]:
    """
    Extract numeric rating from text
    
    Args:
        rating_text: Text containing rating
    
    Returns:
        Extracted rating as float or None
    """
    if pd.isna(rating_text) or rating_text is None:
        return None
    
    # Look for rating patterns like "4.5 out of 5" or "4.5"
    rating_match = re.search(r'(\d+\.?\d*)\s*(?:out\s*of\s*5)?', str(rating_text))
    if rating_match:
        try:
            rating = float(rating_match.group(1))
            return min(max(rating, 0), 5)  # Ensure rating is between 0 and 5
        except ValueError:
            return None
    
    return None


def categorize_price(price: float) -> str:
    """
    Categorize price into budget, mid-range, or premium
    
    Args:
        price: Price value
    
    Returns:
        Price category
    """
    if price is None:
        return "Unknown"
    
    if price < 2000:
        return "Budget"
    elif price < 5000:
        return "Mid-range"
    else:
        return "Premium"


def calculate_discount_percentage(price: float, mrp: float) -> Optional[float]:
    """
    Calculate discount percentage
    
    Args:
        price: Current price
        mrp: Maximum retail price
    
    Returns:
        Discount percentage or None
    """
    if price is None or mrp is None or mrp <= 0:
        return None
    
    discount = ((mrp - price) / mrp) * 100
    return round(discount, 2)


def validate_product_data(df: pd.DataFrame) -> Dict[str, Union[int, List[str]]]:
    """
    Validate product data and return quality metrics
    
    Args:
        df: Product DataFrame
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_records': len(df),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_records': df.duplicated().sum(),
        'issues': []
    }
    
    # Check for required columns
    required_columns = ['title', 'brand', 'price', 'rating']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        results['issues'].append(f"Missing required columns: {missing_columns}")
    
    # Check for invalid ratings
    if 'rating' in df.columns:
        invalid_ratings = df[(df['rating'] < 0) | (df['rating'] > 5)].shape[0]
        if invalid_ratings > 0:
            results['issues'].append(f"Found {invalid_ratings} invalid ratings")
    
    # Check for negative prices
    if 'price' in df.columns:
        negative_prices = df[df['price'] < 0].shape[0]
        if negative_prices > 0:
            results['issues'].append(f"Found {negative_prices} negative prices")
    
    return results


def merge_product_reviews(products_df: pd.DataFrame, reviews_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge product and review DataFrames
    
    Args:
        products_df: Product DataFrame
        reviews_df: Review DataFrame
    
    Returns:
        Merged DataFrame
    """
    return reviews_df.merge(products_df, on='product_id', how='left')
