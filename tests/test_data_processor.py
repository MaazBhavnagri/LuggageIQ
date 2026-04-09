"""
Test data processing functionality
"""

import pytest
import pandas as pd
import numpy as np
from models.data_processor import DataProcessor
from utils.config import Config

def test_data_processor():
    """Test data processing functionality"""
    # Create sample data
    products_data = {
        'product_id': ['p1', 'p2', 'p3'],
        'title': ['Test Product 1', 'Test Product 2', 'Test Product 3'],
        'brand': ['Brand A', 'Brand B', 'Brand A'],
        'price': [1000, 2000, 1500],
        'mrp': [1200, 2500, 1800],
        'rating': [4.5, 3.5, 4.0],
        'review_count': [100, 50, 75]
    }
    
    reviews_data = {
        'review_id': ['r1', 'r2', 'r3'],
        'product_id': ['p1', 'p1', 'p2'],
        'rating': [5, 4, 3],
        'title': ['Great product', 'Good value', 'Average'],
        'text': ['Excellent quality', 'Worth the price', 'Okay product']
    }
    
    products_df = pd.DataFrame(products_data)
    reviews_df = pd.DataFrame(reviews_data)
    
    # Test data processor
    processor = DataProcessor()
    processor.products_df = products_df
    processor.reviews_df = reviews_df
    
    # Test cleaning
    clean_products = processor.clean_products_data()
    clean_reviews = processor.clean_reviews_data()
    
    assert len(clean_products) == 3
    assert len(clean_reviews) == 3
    assert 'price_category' in clean_products.columns
    assert 'sentiment_score' in clean_reviews.columns
    
    print("Data processor tests passed!")

if __name__ == "__main__":
    test_data_processor()
