"""
Test sentiment analysis functionality
"""

import pytest
import pandas as pd
from models.sentiment_analyzer import SentimentAnalyzer

def test_sentiment_analyzer():
    """Test sentiment analysis functionality"""
    # Create sample reviews
    reviews_data = {
        'review_id': ['r1', 'r2', 'r3', 'r4'],
        'product_id': ['p1', 'p1', 'p2', 'p2'],
        'rating': [5, 1, 4, 2],
        'text': [
            'Excellent product, very happy with purchase!',
            'Terrible quality, broke after one use',
            'Good value for money, decent quality',
            'Poor build quality, not recommended'
        ]
    }
    
    reviews_df = pd.DataFrame(reviews_data)
    
    # Test sentiment analyzer
    analyzer = SentimentAnalyzer(method='vader')
    
    # Test single text analysis
    result = analyzer.analyze_text('Great product, love it!')
    assert 'compound' in result
    assert 'positive' in result
    assert 'negative' in result
    assert 'neutral' in result
    
    # Test DataFrame analysis
    analyzed_df = analyzer.analyze_dataframe(reviews_df)
    
    assert 'sentiment_score' in analyzed_df.columns
    assert 'sentiment_label' in analyzed_df.columns
    assert len(analyzed_df) == 4
    
    # Test sentiment classification
    positive_label = analyzer.classify_sentiment(0.5)
    negative_label = analyzer.classify_sentiment(-0.5)
    neutral_label = analyzer.classify_sentiment(0.0)
    
    assert positive_label == 'Positive'
    assert negative_label == 'Negative'
    assert neutral_label == 'Neutral'
    
    print("Sentiment analyzer tests passed!")

if __name__ == "__main__":
    test_sentiment_analyzer()
