"""
API routes for LuggageIQ
"""

import pandas as pd
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from utils.config import Config
from utils.logger import setup_logger
from utils.data_utils import load_data
from models.data_processor import DataProcessor
from models.sentiment_analyzer import SentimentAnalyzer
from models.theme_extractor import ThemeExtractor
from models.pricing_analyzer import PricingAnalyzer
from models.competitive_analyzer import CompetitiveAnalyzer
from models.insights_generator import InsightsGenerator

logger = setup_logger('api_routes')

# Create router
router = APIRouter()

# Global variables for cached data
_cached_data = {
    'products_df': None,
    'reviews_df': None,
    'brand_analysis': None,
    'insights': None,
    'last_updated': None
}


# Pydantic models for API responses
class BrandInfo(BaseModel):
    brand: str
    total_products: int
    avg_price: float
    avg_rating: float
    avg_sentiment: float
    competitive_score: float


class ProductInfo(BaseModel):
    product_id: str
    title: str
    brand: str
    price: float
    rating: float
    review_count: int
    sentiment_score: float
    themes: List[str]


class ReviewInfo(BaseModel):
    review_id: str
    product_id: str
    rating: float
    title: str
    text: str
    sentiment_score: float
    sentiment_label: str
    themes: List[str]


class InsightInfo(BaseModel):
    type: str
    title: str
    description: str
    priority: int
    brand: Optional[str] = None


# Dependency to load data
async def get_data():
    """Load and cache data"""
    global _cached_data
    
    try:
        # Try to load processed data first
        products_file = f"{Config.PROCESSED_DATA_PATH}/products_clean.csv"
        reviews_file = f"{Config.PROCESSED_DATA_PATH}/reviews_clean.csv"
        
        products_df = load_data(products_file)
        reviews_df = load_data(reviews_file)
        
        # If processed data doesn't exist, try raw data
        if products_df.empty or reviews_df.empty:
            products_file = f"{Config.RAW_DATA_PATH}/products.csv"
            reviews_file = f"{Config.RAW_DATA_PATH}/reviews.csv"
            
            products_df = load_data(products_file)
            reviews_df = load_data(reviews_file)
            
            # Process raw data
            processor = DataProcessor()
            processor.products_df = products_df
            processor.reviews_df = reviews_df
            
            products_df = processor.clean_products_data()
            reviews_df = processor.clean_reviews_data()
        
        _cached_data['products_df'] = products_df
        _cached_data['reviews_df'] = reviews_df
        _cached_data['last_updated'] = pd.Timestamp.now()
        
        return products_df, reviews_df
        
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")


async def get_analysis():
    """Get or generate analysis results"""
    global _cached_data
    
    if _cached_data['brand_analysis'] is None:
        products_df, reviews_df = await get_data()
        
        try:
            # Run full analysis
            analyzer = CompetitiveAnalyzer()
            brand_analysis = analyzer.analyze_competitive_landscape(products_df, reviews_df)
            
            # Generate insights
            insights_generator = InsightsGenerator()
            insights = insights_generator.generate_insights(products_df, reviews_df, brand_analysis)
            
            _cached_data['brand_analysis'] = brand_analysis
            _cached_data['insights'] = insights
            
        except Exception as e:
            logger.error(f"Failed to generate analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")
    
    return _cached_data['brand_analysis'], _cached_data['insights']


@router.get("/brands", response_model=List[BrandInfo])
async def get_brands():
    """Get all brands with summary statistics"""
    products_df, reviews_df = await get_data()
    
    brands = []
    try:
        # Simple brand aggregation without competitive analysis
        brand_summary = products_df.groupby('brand').agg({
            'price': ['mean', 'count'],
            'rating': 'mean',
            'review_count': 'sum'
        }).round(2)
        
        # Handle NaN values
        brand_summary = brand_summary.fillna(0)
        
        # Flatten column names
        brand_summary.columns = ['_'.join(col).strip() for col in brand_summary.columns]
        brand_summary = brand_summary.reset_index()
        
        # Calculate sentiment per brand
        brand_sentiment = {}
        try:
            if 'sentiment_score' in reviews_df.columns:
                brand_sentiment = reviews_df.groupby('product_id')['sentiment_score'].mean()
                # Map to brands
                product_to_brand = dict(zip(products_df['product_id'], products_df['brand']))
                brand_sentiment = reviews_df.groupby('product_id')['sentiment_score'].mean().to_dict()
                brand_sentiment = {}
                for product_id, sentiment in reviews_df.groupby('product_id')['sentiment_score'].mean().items():
                    brand = products_df[products_df['product_id'] == product_id]['brand'].iloc[0]
                    if brand not in brand_sentiment:
                        brand_sentiment[brand] = []
                    brand_sentiment[brand].append(sentiment)
                
                brand_sentiment = {brand: sum(sentiments)/len(sentiments) for brand, sentiments in brand_sentiment.items()}
        except Exception:
            brand_sentiment = {}
        
        for _, row in brand_summary.iterrows():
            brand = row['brand']
            avg_sentiment = float(brand_sentiment.get(brand, 0))
            
            brand_info = BrandInfo(
                brand=brand,
                total_products=int(row['price_count']),
                avg_price=float(row['price_mean']),
                avg_rating=float(row['rating']),
                avg_sentiment=avg_sentiment,
                competitive_score=float(row['price_mean'])  # Using price as placeholder
            )
            brands.append(brand_info)
            
    except Exception as e:
        logger.error(f"Error in brands endpoint: {e}")
        # Fallback to basic brand list
        unique_brands = products_df['brand'].unique()
        for brand in unique_brands:
            brand_data = products_df[products_df['brand'] == brand]
            brand_info = BrandInfo(
                brand=brand,
                total_products=len(brand_data),
                avg_price=float(brand_data['price'].mean()),
                avg_rating=float(brand_data['rating'].mean()),
                avg_sentiment=0.0,
                competitive_score=float(brand_data['price'].mean())
            )
            brands.append(brand_info)
    
    return brands


@router.get("/brands/{brand_name}")
async def get_brand_details(brand_name: str):
    """Get detailed information for a specific brand"""
    products_df, reviews_df = await get_data()
    
    # Check if brand exists
    if brand_name not in products_df['brand'].unique():
        raise HTTPException(status_code=404, detail=f"Brand '{brand_name}' not found")
    
    # Get brand data
    brand_products = products_df[products_df['brand'] == brand_name]
    brand_reviews = reviews_df[reviews_df['product_id'].isin(brand_products['product_id'])]
    
    # Calculate metrics
    summary = {
        'brand': brand_name,
        'total_products': len(brand_products),
        'total_reviews': len(brand_reviews),
        'avg_price': float(brand_products['price'].mean()),
        'avg_rating': float(brand_products['rating'].mean()),
        'avg_sentiment': 0.0
    }
    
    # Calculate sentiment if available
    try:
        if 'sentiment_score' in brand_reviews.columns:
            summary['avg_sentiment'] = float(brand_reviews['sentiment_score'].mean())
    except Exception:
        pass
    
    # Get top products for brand
    top_products = []
    try:
        brand_products_sorted = brand_products.sort_values(['rating', 'review_count'], ascending=[False, False]).head(5)
        for _, product in brand_products_sorted.iterrows():
            top_products.append({
                'product_id': product['product_id'],
                'title': product['title'],
                'price': float(product['price']),
                'rating': float(product['rating']),
                'review_count': int(product['review_count'])
            })
    except Exception:
        pass
    
    return {
        'brand': brand_name,
        'summary': {
            'competitive_rank': 1,  # Placeholder
            'competitive_score': summary['avg_price'],
            'value_score': summary['avg_price'],
            'market_position': 'Unknown'
        },
        'metrics': {
            'total_products': summary['total_products'],
            'total_reviews': summary['total_reviews'],
            'avg_price': summary['avg_price'],
            'avg_rating': summary['avg_rating'],
            'avg_sentiment': summary['avg_sentiment'],
            'avg_discount': float(brand_products['discount_pct'].mean()) if 'discount_pct' in brand_products.columns else 0.0
        },
        'strengths': [],
        'weaknesses': [],
        'customer_feedback': {},
        'top_products': top_products
    }


def _get_top_products_for_brand(products_df: pd.DataFrame, brand: str, limit: int = 5):
    """Get top products for a brand"""
    brand_products = products_df[products_df['brand'] == brand]
    
    # Sort by rating and review count
    top_products = brand_products.sort_values(['rating', 'review_count'], ascending=[False, False]).head(limit)
    
    return [
        {
            'product_id': row['product_id'],
            'title': row['title'],
            'price': float(row.get('price', 0)),
            'rating': float(row.get('rating', 0)),
            'review_count': int(row.get('review_count', 0)),
            'value_score': float(row.get('value_score', 0))
        }
        for _, row in top_products.iterrows()
    ]


@router.get("/products")
async def get_products(
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    min_rating: Optional[float] = Query(None, description="Minimum rating filter"),
    limit: int = Query(50, description="Maximum number of products to return"),
    offset: int = Query(0, description="Number of products to skip")
):
    """Get products with optional filters"""
    products_df, reviews_df = await get_data()
    
    # Apply filters
    filtered_df = products_df.copy()
    
    if brand:
        filtered_df = filtered_df[filtered_df['brand'] == brand]
    
    if min_price:
        filtered_df = filtered_df[filtered_df['price'] >= min_price]
    
    if max_price:
        filtered_df = filtered_df[filtered_df['price'] <= max_price]
    
    if min_rating:
        filtered_df = filtered_df[filtered_df['rating'] >= min_rating]
    
    # Apply pagination
    total_count = len(filtered_df)
    filtered_df = filtered_df.iloc[offset:offset + limit]
    
    products = []
    for _, row in filtered_df.iterrows():
        # Handle missing columns safely
        sentiment_score = 0.0
        themes = []
        
        # Try to get sentiment and themes from reviews if available
        try:
            if 'sentiment_score' in row:
                sentiment_score = float(row['sentiment_score'])
            elif 'product_id' in row:
                # Get sentiment from reviews for this product
                product_reviews = reviews_df[reviews_df['product_id'] == row['product_id']]
                if 'sentiment_score' in product_reviews.columns and not product_reviews.empty:
                    sentiment_score = float(product_reviews['sentiment_score'].mean())
            
            if 'themes' in row:
                themes = row['themes'] if isinstance(row['themes'], list) else []
            elif 'product_id' in row:
                # Get themes from reviews for this product
                product_reviews = reviews_df[reviews_df['product_id'] == row['product_id']]
                if 'themes' in product_reviews.columns and not product_reviews.empty:
                    all_themes = []
                    for theme_list in product_reviews['themes'].dropna():
                        if isinstance(theme_list, str):
                            # Handle string representation of list
                            try:
                                theme_list = eval(theme_list) if theme_list.startswith('[') else theme_list.split(',')
                                all_themes.extend(theme_list)
                            except:
                                all_themes.append(theme_list)
                        elif isinstance(theme_list, list):
                            all_themes.extend(theme_list)
                    themes = list(set(all_themes))  # Remove duplicates
        except Exception:
            pass
        
        product_info = ProductInfo(
            product_id=row['product_id'],
            title=row['title'],
            brand=row['brand'],
            price=float(row.get('price', 0)),
            rating=float(row.get('rating', 0)),
            review_count=int(row.get('review_count', 0)),
            sentiment_score=sentiment_score,
            themes=themes
        )
        products.append(product_info)
    
    return {
        'products': products,
        'total_count': total_count,
        'limit': limit,
        'offset': offset
    }


@router.get("/products/{product_id}")
async def get_product_details(product_id: str):
    """Get detailed information for a specific product"""
    products_df, reviews_df = await get_data()
    
    # Find product
    product_data = products_df[products_df['product_id'] == product_id]
    
    if product_data.empty:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    
    product = product_data.iloc[0]
    
    # Get product reviews
    product_reviews = reviews_df[reviews_df['product_id'] == product_id]
    
    return {
        'product': {
            'product_id': product['product_id'],
            'title': product['title'],
            'brand': product['brand'],
            'price': float(product.get('price', 0)),
            'mrp': float(product.get('mrp', 0)),
            'discount_pct': float(product.get('discount_pct', 0)),
            'rating': float(product.get('rating', 0)),
            'review_count': int(product.get('review_count', 0)),
            'price_category': product.get('price_category', 'Unknown'),
            'value_score': float(product.get('value_score', 0))
        },
        'sentiment_summary': {
            'avg_sentiment': float(product_reviews['sentiment_score'].mean()) if len(product_reviews) > 0 else 0,
            'positive_reviews': int((product_reviews['sentiment_label'] == 'Positive').sum()),
            'negative_reviews': int((product_reviews['sentiment_label'] == 'Negative').sum()),
            'neutral_reviews': int((product_reviews['sentiment_label'] == 'Neutral').sum())
        },
        'theme_summary': _get_theme_summary_for_product(product_reviews),
        'recent_reviews': _get_recent_reviews_for_product(product_reviews, limit=5)
    }


def _get_theme_summary_for_product(reviews_df: pd.DataFrame):
    """Get theme summary for product reviews"""
    all_themes = []
    for themes in reviews_df['themes'].dropna():
        if isinstance(themes, list):
            all_themes.extend(themes)
    
    from collections import Counter
    theme_counts = Counter(all_themes)
    
    return {
        'top_themes': [
            {'theme': theme, 'count': count}
            for theme, count in theme_counts.most_common(5)
        ]
    }


def _get_recent_reviews_for_product(reviews_df: pd.DataFrame, limit: int = 5):
    """Get recent reviews for product"""
    recent_reviews = reviews_df.head(limit)  # Assuming data is ordered by recency
    
    return [
        {
            'review_id': row['review_id'],
            'rating': float(row['rating']),
            'title': row.get('title', ''),
            'text': row.get('text', ''),
            'sentiment_score': float(row.get('sentiment_score', 0)),
            'sentiment_label': row.get('sentiment_label', 'Unknown'),
            'themes': row.get('themes', [])
        }
        for _, row in recent_reviews.iterrows()
    ]


@router.get("/reviews")
async def get_reviews(
    brand: Optional[str] = Query(None, description="Filter by brand"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (Positive/Negative/Neutral)"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
    min_rating: Optional[float] = Query(None, description="Minimum rating filter"),
    max_rating: Optional[float] = Query(None, description="Maximum rating filter"),
    limit: int = Query(50, description="Maximum number of reviews to return"),
    offset: int = Query(0, description="Number of reviews to skip")
):
    """Get reviews with optional filters"""
    products_df, reviews_df = await get_data()
    
    # Merge with products to get brand information
    merged_df = reviews_df.merge(
        products_df[['product_id', 'brand']], 
        on='product_id', 
        how='left'
    )
    
    # Apply filters
    filtered_df = merged_df.copy()
    
    if brand:
        filtered_df = filtered_df[filtered_df['brand'] == brand]
    
    if sentiment:
        filtered_df = filtered_df[filtered_df['sentiment_label'] == sentiment]
    
    if theme:
        # Filter reviews that contain the specified theme
        filtered_df = filtered_df[
            filtered_df['themes'].apply(
                lambda x: isinstance(x, list) and theme in x
            )
        ]
    
    if min_rating:
        filtered_df = filtered_df[filtered_df['rating'] >= min_rating]
    
    if max_rating:
        filtered_df = filtered_df[filtered_df['rating'] <= max_rating]
    
    # Apply pagination
    total_count = len(filtered_df)
    filtered_df = filtered_df.iloc[offset:offset + limit]
    
    reviews = []
    for _, row in filtered_df.iterrows():
        # Handle themes properly
        themes = []
        try:
            if 'themes' in row and row['themes']:
                if isinstance(row['themes'], str):
                    # Handle string representation of list
                    if row['themes'].startswith('['):
                        themes = eval(row['themes'])
                    else:
                        themes = row['themes'].split(',')
                elif isinstance(row['themes'], list):
                    themes = row['themes']
                # Ensure themes is a list of strings
                themes = [str(theme).strip() for theme in themes if theme]
        except Exception:
            themes = []
        
        review_info = {
            'review_id': row['review_id'],
            'product_id': row['product_id'],
            'rating': float(row['rating']),
            'title': row.get('title', ''),
            'text': row.get('text', ''),
            'sentiment_score': float(row.get('sentiment_score', 0)),
            'sentiment_label': row.get('sentiment_label', 'Unknown'),
            'themes': themes
        }
        reviews.append(review_info)
    
    return {
        'reviews': reviews,
        'total_count': total_count,
        'limit': limit,
        'offset': offset
    }


@router.get("/analysis/summary")
async def get_analysis_summary():
    """Get overall analysis summary"""
    products_df, reviews_df = await get_data()
    
    # Basic overview with safe column access
    overview = {
        'total_brands': products_df['brand'].nunique(),
        'total_products': len(products_df),
        'total_reviews': len(reviews_df),
        'avg_price': float(products_df['price'].mean()),
        'avg_rating': float(products_df['rating'].mean()),
        'avg_sentiment': 0.0,
        'data_last_updated': _cached_data['last_updated'].isoformat() if _cached_data['last_updated'] else None
    }
    
    # Safe sentiment calculation
    try:
        if 'sentiment_score' in reviews_df.columns:
            overview['avg_sentiment'] = float(reviews_df['sentiment_score'].mean())
    except Exception:
        pass
    
    # Simple brand summary
    top_brands = []
    try:
        brand_counts = products_df['brand'].value_counts().head(5)
        for brand, count in brand_counts.items():
            brand_data = products_df[products_df['brand'] == brand]
            avg_price = float(brand_data['price'].mean())
            avg_rating = float(brand_data['rating'].mean())
            
            top_brands.append({
                'brand': brand,
                'competitive_score': avg_price,
                'avg_price': avg_price,
                'avg_rating': avg_rating,
                'total_products': int(count)
            })
    except Exception as e:
        logger.error(f"Error in brand summary: {e}")
    
    # Simple distributions
    price_dist = {'min_price': float(products_df['price'].min()), 'max_price': float(products_df['price'].max())}
    sentiment_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    try:
        if 'sentiment_label' in reviews_df.columns:
            sentiment_dist = reviews_df['sentiment_label'].value_counts().to_dict()
            # Convert to int
            for key in sentiment_dist:
                sentiment_dist[key] = int(sentiment_dist[key])
    except Exception:
        pass
    
    return {
        'overview': overview,
        'top_brands': top_brands,
        'price_distribution': price_dist,
        'sentiment_distribution': sentiment_dist
    }


def _get_top_brands_summary(competitive_scores: pd.DataFrame, limit: int = 5):
    """Get summary of top brands"""
    top_brands = competitive_scores.head(limit)
    
    return [
        {
            'rank': int(row['competitive_rank']),
            'brand': row['brand'],
            'competitive_score': float(row['competitive_score']),
            'value_score': float(row['value_score']),
            'avg_price': float(row.get('avg_price', 0)),
            'avg_rating': float(row.get('avg_rating', 0))
        }
        for _, row in top_brands.iterrows()
    ]


def _get_price_distribution_summary(products_df: pd.DataFrame):
    """Get price distribution summary"""
    return {
        'min_price': float(products_df['price'].min()),
        'max_price': float(products_df['price'].max()),
        'median_price': float(products_df['price'].median()),
        'avg_price': float(products_df['price'].mean()),
        'categories': products_df['price_category'].value_counts().to_dict()
    }


def _get_sentiment_distribution_summary(reviews_df: pd.DataFrame):
    """Get sentiment distribution summary"""
    return {
        'avg_sentiment': float(reviews_df['sentiment_score'].mean()),
        'positive_count': int((reviews_df['sentiment_label'] == 'Positive').sum()),
        'negative_count': int((reviews_df['sentiment_label'] == 'Negative').sum()),
        'neutral_count': int((reviews_df['sentiment_label'] == 'Neutral').sum()),
        'distribution': reviews_df['sentiment_label'].value_counts().to_dict()
    }


@router.get("/insights")
async def get_insights(
    type: Optional[str] = Query(None, description="Filter by insight type"),
    limit: int = Query(20, description="Maximum number of insights to return")
):
    """Get AI-generated insights"""
    products_df, reviews_df = await get_data()
    
    # Generate simple insights based on data
    insights = []
    
    try:
        # Best value brand
        brand_summary = products_df.groupby('brand').agg({
            'price': 'mean',
            'rating': 'mean',
            'review_count': 'sum'
        }).round(2)
        
        brand_summary['value_score'] = brand_summary['rating'] / (brand_summary['price'] / 1000)
        best_value_brand = brand_summary['value_score'].idxmax()
        
        insights.append({
            'id': 'best_value',
            'title': f'Best Value Brand: {best_value_brand}',
            'description': f'{best_value_brand} offers the best value for money with high ratings at competitive prices.',
            'type': 'Value Analysis',
            'priority': 9,
            'brand': best_value_brand
        })
        
        # Highest rated brand
        highest_rated = brand_summary['rating'].idxmax()
        insights.append({
            'id': 'highest_rated',
            'title': f'Highest Rated Brand: {highest_rated}',
            'description': f'{highest_rated} has the highest average customer rating among all brands.',
            'type': 'Quality Analysis',
            'priority': 8,
            'brand': highest_rated
        })
        
        # Most reviews brand
        most_reviews = brand_summary['review_count'].idxmax()
        insights.append({
            'id': 'most_reviews',
            'title': f'Most Reviewed Brand: {most_reviews}',
            'description': f'{most_reviews} has the most customer reviews, indicating high market engagement.',
            'type': 'Market Analysis',
            'priority': 7,
            'brand': most_reviews
        })
        
        # Overall market insight
        avg_rating = products_df['rating'].mean()
        avg_price = products_df['price'].mean()
        
        insights.append({
            'id': 'market_overview',
            'title': 'Market Overview',
            'description': f'The luggage market has an average rating of {avg_rating:.1f}/5 with average price of ${avg_price:.0f}. Quality varies significantly across brands.',
            'type': 'Market Analysis',
            'priority': 5,
            'brand': None
        })
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        # Fallback insights
        insights = [
            {
                'id': 'fallback_1',
                'title': 'Market Analysis Available',
                'description': 'Competitive analysis is available for all major luggage brands.',
                'type': 'General',
                'priority': 5,
                'brand': None
            }
        ]
    
    # Filter insights by type if specified
    if type:
        filtered_insights = [insight for insight in insights if insight.get('type') == type]
    else:
        filtered_insights = insights
    
    # Limit results
    filtered_insights = filtered_insights[:limit]
    
    return filtered_insights


@router.get("/compare")
async def compare_brands(
    brands: List[str] = Query(..., description="List of brands to compare")
):
    """Compare multiple brands side-by-side"""
    products_df, reviews_df = await get_data()
    
    # Validate brands
    available_brands = products_df['brand'].unique().tolist()
    invalid_brands = [brand for brand in brands if brand not in available_brands]
    if invalid_brands:
        raise HTTPException(
            status_code=400, 
            detail=f"Brands not found: {', '.join(invalid_brands)}"
        )
    
    # Generate simple comparison
    comparison_data = {
        'brands': brands,
        'metrics': {
            'competitive_score': {},
            'value_score': {},
            'avg_price': {},
            'avg_rating': {},
            'total_products': {},
            'total_reviews': {},
            'avg_sentiment': {}
        },
        'ranking': {
            'competitive': brands,
            'value': brands,
            'price': brands
        }
    }
    
    # Calculate metrics for each brand
    for brand in brands:
        brand_products = products_df[products_df['brand'] == brand]
        brand_reviews = reviews_df[reviews_df['product_id'].isin(brand_products['product_id'])]
        
        # Calculate metrics
        avg_price = float(brand_products['price'].mean())
        avg_rating = float(brand_products['rating'].mean())
        total_products = len(brand_products)
        total_reviews = len(brand_reviews)
        
        # Calculate sentiment
        avg_sentiment = 0.0
        try:
            if 'sentiment_score' in brand_reviews.columns and not brand_reviews.empty:
                avg_sentiment = float(brand_reviews['sentiment_score'].mean())
        except Exception:
            pass
        
        # Simple competitive and value scores based on price and rating
        competitive_score = avg_price  # Using price as placeholder
        value_score = avg_rating * 1000  # Simple value calculation
        
        comparison_data['metrics']['competitive_score'][brand] = competitive_score
        comparison_data['metrics']['value_score'][brand] = value_score
        comparison_data['metrics']['avg_price'][brand] = avg_price
        comparison_data['metrics']['avg_rating'][brand] = avg_rating
        comparison_data['metrics']['total_products'][brand] = total_products
        comparison_data['metrics']['total_reviews'][brand] = total_reviews
        comparison_data['metrics']['avg_sentiment'][brand] = avg_sentiment
    
    # Sort rankings
    comparison_data['ranking']['competitive'] = sorted(brands, key=lambda x: comparison_data['metrics']['competitive_score'][x], reverse=True)
    comparison_data['ranking']['value'] = sorted(brands, key=lambda x: comparison_data['metrics']['value_score'][x], reverse=True)
    comparison_data['ranking']['price'] = sorted(brands, key=lambda x: comparison_data['metrics']['avg_price'][x])
    
    return comparison_data


@router.get("/search")
async def search_products(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search products by title or brand"""
    products_df, reviews_df = await get_data()
    
    # Simple text search
    query_lower = query.lower()
    mask = (
        products_df['title'].str.lower().str.contains(query_lower, na=False) |
        products_df['brand'].str.lower().str.contains(query_lower, na=False)
    )
    
    results = products_df[mask].head(limit)
    
    return {
        'query': query,
        'results': [
            {
                'product_id': row['product_id'],
                'title': row['title'],
                'brand': row['brand'],
                'price': float(row.get('price', 0)),
                'rating': float(row.get('rating', 0)),
                'review_count': int(row.get('review_count', 0))
            }
            for _, row in results.iterrows()
        ],
        'total_count': len(results)
    }


@router.get("/stats")
async def get_statistics():
    """Get detailed statistics for the dashboard"""
    products_df, reviews_df = await get_data()
    
    return {
        'products': {
            'total': len(products_df),
            'by_brand': products_df['brand'].value_counts().to_dict(),
            'by_category': products_df['price_category'].value_counts().to_dict(),
            'price_stats': {
                'mean': float(products_df['price'].mean()),
                'median': float(products_df['price'].median()),
                'std': float(products_df['price'].std()),
                'min': float(products_df['price'].min()),
                'max': float(products_df['price'].max())
            },
            'rating_stats': {
                'mean': float(products_df['rating'].mean()),
                'median': float(products_df['rating'].median()),
                'std': float(products_df['rating'].std()),
                'min': float(products_df['rating'].min()),
                'max': float(products_df['rating'].max())
            }
        },
        'reviews': {
            'total': len(reviews_df),
            'by_sentiment': reviews_df['sentiment_label'].value_counts().to_dict(),
            'by_rating': reviews_df['rating'].value_counts().to_dict(),
            'sentiment_stats': {
                'mean': float(reviews_df['sentiment_score'].mean()),
                'median': float(reviews_df['sentiment_score'].median()),
                'std': float(reviews_df['sentiment_score'].std()),
                'min': float(reviews_df['sentiment_score'].min()),
                'max': float(reviews_df['sentiment_score'].max())
            }
        },
        'themes': {
            'total_themes': len(reviews_df[reviews_df['themes'].notna()]),
            'top_themes': _get_global_theme_stats(reviews_df)
        }
    }


def _get_global_theme_stats(reviews_df: pd.DataFrame):
    """Get global theme statistics"""
    all_themes = []
    for themes in reviews_df['themes'].dropna():
        if isinstance(themes, list):
            all_themes.extend(themes)
    
    from collections import Counter
    theme_counts = Counter(all_themes)
    
    return [
        {'theme': theme, 'count': count}
        for theme, count in theme_counts.most_common(10)
    ]
