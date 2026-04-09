"""
System test for LuggageIQ - tests core functionality
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from utils.config import Config
        from utils.logger import setup_logger
        from utils.data_utils import clean_text, extract_price
        print("  Utils modules imported successfully")
    except Exception as e:
        print(f"  Utils import failed: {e}")
        return False
    
    try:
        from models.data_processor import DataProcessor
        from models.sentiment_analyzer import SentimentAnalyzer
        from models.theme_extractor import ThemeExtractor
        print("  Models modules imported successfully")
    except Exception as e:
        print(f"  Models import failed: {e}")
        return False
    
    try:
        from scraper.amazon_scraper import AmazonScraper
        print("  Scraper module imported successfully")
    except Exception as e:
        print(f"  Scraper import failed: {e}")
        return False
    
    try:
        from api.main import app
        print("  API module imported successfully")
    except Exception as e:
        print(f"  API import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    print("\nTesting basic functionality...")
    
    try:
        # Test config
        from utils.config import Config
        Config.ensure_directories()
        print("  Config and directories created successfully")
    except Exception as e:
        print(f"  Config test failed: {e}")
        return False
    
    try:
        # Test data utils
        from utils.data_utils import clean_text, extract_price, extract_rating
        
        test_text = "  This is a test!  "
        cleaned = clean_text(test_text)
        assert cleaned == "This is a test"
        
        price = extract_price("$1,234.56")
        assert price == 1234.56
        
        rating = extract_rating("4.5 out of 5 stars")
        assert rating == 4.5
        
        print("  Data utilities working correctly")
    except Exception as e:
        print(f"  Data utils test failed: {e}")
        return False
    
    try:
        # Test sentiment analyzer
        from models.sentiment_analyzer import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer(method='vader')
        result = analyzer.analyze_text("Great product, love it!")
        
        assert 'compound' in result
        assert 'positive' in result
        assert 'negative' in result
        assert 'neutral' in result
        
        # Test classification
        pos_label = analyzer.classify_sentiment(0.5)
        neg_label = analyzer.classify_sentiment(-0.5)
        neu_label = analyzer.classify_sentiment(0.0)
        
        assert pos_label == 'Positive'
        assert neg_label == 'Negative'
        assert neu_label == 'Neutral'
        
        print("  Sentiment analyzer working correctly")
    except Exception as e:
        print(f"  Sentiment analyzer test failed: {e}")
        return False
    
    try:
        # Test theme extractor
        from models.theme_extractor import ThemeExtractor
        
        extractor = ThemeExtractor(method='keyword')
        themes = extractor.extract_themes_keyword("The wheels are great but the handle broke")
        
        assert isinstance(themes, dict)
        print("  Theme extractor working correctly")
    except Exception as e:
        print(f"  Theme extractor test failed: {e}")
        return False
    
    return True

def test_data_processing():
    """Test data processing with sample data"""
    print("\nTesting data processing...")
    
    try:
        import pandas as pd
        from models.data_processor import DataProcessor
        
        # Create sample data
        products_data = {
            'product_id': ['p1', 'p2', 'p3'],
            'title': ['Test Product 1', 'Test Product 2', 'Test Product 3'],
            'brand': ['Brand A', 'Brand B', 'Brand A'],
            'price': [1000, 2000, 1500],
            'mrp': [1200, 2500, 1800],
            'discount_pct': [16.7, 20.0, 16.7],  # Add this column
            'rating': [4.5, 3.5, 4.0],
            'review_count': [100, 50, 75]
        }
        
        reviews_data = {
            'review_id': ['r1', 'r2', 'r3'],
            'product_id': ['p1', 'p1', 'p2'],
            'rating': [5, 4, 3],
            'title': ['Great product', 'Good value', 'Average'],
            'text': ['Excellent quality', 'Worth the price', 'Okay product'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03']
        }
        
        products_df = pd.DataFrame(products_data)
        reviews_df = pd.DataFrame(reviews_data)
        
        # Test processing
        processor = DataProcessor()
        processor.products_df = products_df
        processor.reviews_df = reviews_df
        
        clean_products = processor.clean_products_data()
        clean_reviews = processor.clean_reviews_data()
        
        assert len(clean_products) == 3
        assert len(clean_reviews) == 3
        assert 'price_category' in clean_products.columns
        assert 'sentiment_score' in clean_reviews.columns
        
        print("  Data processing working correctly")
        return True
        
    except Exception as e:
        print(f"  Data processing test failed: {e}")
        return False

def test_project_structure():
    """Test that project structure is complete"""
    print("\nTesting project structure...")
    
    required_dirs = [
        'scraper', 'data', 'models', 'api', 'dashboard', 
        'utils', 'tests', 'notebooks', 'scripts'
    ]
    
    required_files = [
        'requirements.txt', 'README.md', 'QUICK_START.md',
        'scraper/main.py', 'api/main.py', 'dashboard/app.py',
        'utils/config.py', 'models/data_processor.py'
    ]
    
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"  Missing directory: {dir_name}")
            return False
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"  Missing file: {file_path}")
            return False
    
    print("  Project structure complete")
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("LUGGAGEIQ SYSTEM TEST")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Data Processing", test_data_processing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                print(f"  PASSED")
                passed += 1
            else:
                print(f"  FAILED")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run setup: python scripts/setup_environment.py")
        print("2. Run pipeline: python scripts/run_full_pipeline.py")
        print("3. Start API: python api/main.py")
        print("4. Start dashboard: streamlit run dashboard/app.py")
    else:
        print("Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
