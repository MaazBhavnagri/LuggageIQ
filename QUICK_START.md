# LuggageIQ - Quick Start Guide

## Overview

LuggageIQ is a comprehensive competitive intelligence system for Amazon India luggage brands. It scrapes product data, analyzes customer sentiment, extracts themes, and provides actionable insights through an interactive dashboard.

## Quick Setup

### 1. Environment Setup

```bash
# Clone the repository (if applicable)
cd LuggageIQ

# Run the setup script
python scripts/setup_environment.py
```

### 2. Run the Complete Pipeline

```bash
# Run everything from scraping to insights
python scripts/run_full_pipeline.py

# Or specify brands and products per brand
python scripts/run_full_pipeline.py --brands Safari Skybags --products-per-brand 10
```

### 3. Start Services

#### Option A: Start Backend API
```bash
python api/main.py
# API will be available at http://localhost:8000
```

#### Option B: Start Dashboard
```bash
streamlit run dashboard/app.py
# Dashboard will be available at http://localhost:8501
```

## What LuggageIQ Does

### 1. Data Scraping
- Scrapes Amazon India for luggage products
- Extracts product details (price, rating, reviews)
- Downloads customer reviews for sentiment analysis

### 2. Data Processing
- Cleans and standardizes scraped data
- Removes duplicates and handles missing values
- Calculates derived metrics (discounts, value scores)

### 3. Sentiment Analysis
- Analyzes customer review sentiment using VADER
- Classifies reviews as Positive, Negative, or Neutral
- Detects rating-sentiment anomalies

### 4. Theme Extraction
- Identifies common themes in reviews:
  - Wheels, Handle, Zipper, Durability
  - Space/Capacity, Material, Weight, etc.
- Groups complaints and praises by category

### 5. Competitive Analysis
- Compares brands across multiple dimensions
- Calculates competitive and value scores
- Identifies market positioning

### 6. AI Insights
- Generates actionable insights automatically:
  - Best value brands
  - Rating-sentiment mismatches
  - High complaint categories
  - Market gaps and opportunities

## Dashboard Features

### Overview Page
- Total brands, products, reviews
- Average sentiment and ratings
- Top performing brands
- Market positioning summary

### Brand Comparison
- Side-by-side brand analysis
- Competitive and value scores
- Detailed metrics comparison
- Rankings by different criteria

### Products Page
- Filter by brand, price, rating
- Product details and themes
- Price vs rating analysis
- Value score rankings

### Reviews Page
- Filter by brand, sentiment, theme
- Customer review analysis
- Sentiment distribution
- Theme-based insights

### Insights Page
- AI-generated insights
- Priority-based recommendations
- Market opportunities
- Strategic recommendations

### Search Page
- Search products by title/brand
- Quick product lookup
- Review analysis

## API Endpoints

### Core Endpoints
- `GET /api/v1/brands` - List all brands
- `GET /api/v1/brands/{brand}` - Brand details
- `GET /api/v1/products` - List products with filters
- `GET /api/v1/reviews` - List reviews with filters
- `GET /api/v1/insights` - AI-generated insights

### Analysis Endpoints
- `GET /api/v1/analysis/summary` - Overall summary
- `GET /api/v1/compare` - Compare brands
- `GET /api/v1/search` - Search products
- `GET /api/v1/stats` - Detailed statistics

## Sample Usage

### Using the API
```python
import requests

# Get brand list
response = requests.get('http://localhost:8000/api/v1/brands')
brands = response.json()

# Compare brands
response = requests.get('http://localhost:8000/api/v1/compare', 
                       params={'brands': ['Safari', 'Skybags']})
comparison = response.json()

# Get insights
response = requests.get('http://localhost:8000/api/v1/insights')
insights = response.json()
```

### Using the Data Directly
```python
from models.data_processor import DataProcessor
from models.sentiment_analyzer import SentimentAnalyzer

# Load processed data
processor = DataProcessor()
processor.load_raw_data()
products_df, reviews_df = processor.process_scraped_data()

# Analyze sentiment
analyzer = SentimentAnalyzer()
reviews_with_sentiment = analyzer.analyze_dataframe(reviews_df)
```

## Configuration

### Environment Variables (.env)
```env
# Scraping
SCRAPING_DELAY=2
MAX_RETRIES=3
REVIEW_COUNT_PER_PRODUCT=50

# API
API_HOST=0.0.0.0
API_PORT=8000

# Dashboard
DASHBOARD_PORT=8501
```

### Supported Brands
- Safari
- Skybags
- American Tourister
- VIP
- Samsonite
- Wildcraft
- And more...

## Data Structure

### Products
- product_id, title, brand, price, mrp, discount_pct
- rating, review_count, price_category, value_score

### Reviews
- review_id, product_id, rating, title, text
- sentiment_score, sentiment_label, themes

### Analysis
- Competitive scores, brand rankings
- Market positioning, insights
- Theme analysis, pricing patterns

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure backend is running: `python api/main.py`
   - Check port 8000 is available

2. **Scraping Issues**
   - Install Playwright: `python -m playwright install`
   - Check internet connection
   - Try with fewer brands/products

3. **Data Not Available**
   - Run the pipeline first: `python scripts/run_full_pipeline.py`
   - Check data files in `data/processed/`

4. **Dashboard Errors**
   - Ensure API is running first
   - Check browser console for errors
   - Restart both services

### Getting Help

1. Check logs in `logs/luggageiq.log`
2. Run tests: `python tests/test_data_processor.py`
3. Try sample analysis: `python notebooks/sample_analysis.py`

## Next Steps

1. **Custom Analysis**: Use the API for custom queries
2. **Additional Brands**: Modify scraper for new brands
3. **Advanced Insights**: Extend the insights generator
4. **Data Export**: Use processed data for external analysis

## Production Deployment

For production use:
1. Use a proper web server (Gunicorn/Nginx)
2. Set up database instead of CSV files
3. Add authentication and rate limiting
4. Configure proper logging and monitoring
5. Set up automated data refresh

---

**LuggageIQ** - Transforming luggage market intelligence with AI
