"""
Main Streamlit dashboard for LuggageIQ
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))  # Change working directory to project root

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from typing import List, Dict, Optional
import time

from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger('dashboard')

# Configure Streamlit page
st.set_page_config(
    page_title="LuggageIQ - Competitive Intelligence Dashboard",
    page_icon=" suitcase",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .insight-card {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .brand-comparison {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def fetch_api_data(endpoint: str, params: Dict = None) -> Dict:
    """Fetch data from API"""
    try:
        # Handle health endpoint separately
        if endpoint == "/health":
            url = "http://localhost:8000/health"
        else:
            url = f"{API_BASE_URL}{endpoint}"
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {str(e)}")
        return {}
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return {}


def load_data():
    """Load initial data"""
    # Try to load summary data
    summary = fetch_api_data("/analysis/summary")
    if not summary:
        st.error("Unable to connect to the API. Please make sure the backend is running.")
        st.stop()
    
    return summary


def render_overview_page(summary: Dict):
    """Render overview page"""
    st.markdown('<h1 class="main-header">LuggageIQ Dashboard</h1>', unsafe_allow_html=True)
    
    # Key metrics
    overview = summary.get('overview', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{overview.get('total_brands', 0)}</h3>
            <p>Total Brands</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{overview.get('total_products', 0)}</h3>
            <p>Total Products</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{overview.get('total_reviews', 0)}</h3>
            <p>Total Reviews</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_sentiment = overview.get('avg_sentiment', 0)
        sentiment_color = "green" if avg_sentiment > 0.1 else "red" if avg_sentiment < -0.1 else "orange"
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {sentiment_color}">{avg_sentiment:.2f}</h3>
            <p>Avg Sentiment</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Top brands
    top_brands = summary.get('top_brands', [])
    if top_brands:
        st.subheader("Top Performing Brands")
        
        brand_df = pd.DataFrame(top_brands)
        
        fig = go.Figure(data=[
            go.Bar(
                x=brand_df['brand'],
                y=brand_df['competitive_score'],
                text=brand_df['competitive_score'].round(1),
                textposition='auto',
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            title="Competitive Scores",
            xaxis_title="Brand",
            yaxis_title="Competitive Score",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Market positioning
    positioning = summary.get('market_positioning', {})
    if positioning:
        st.subheader("Market Positioning")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if positioning.get('market_leaders'):
                st.write("**Market Leaders:**")
                for leader in positioning['market_leaders'][:3]:
                    st.write(f"- {leader.get('brand', 'Unknown')}: {leader.get('competitive_score', 0):.1f}")
        
        with col2:
            if positioning.get('value_champions'):
                st.write("**Value Champions:**")
                for champion in positioning['value_champions'][:3]:
                    st.write(f"- {champion.get('brand', 'Unknown')}: {champion.get('value_score', 0):.1f}")
    
    # Price and sentiment distribution
    col1, col2 = st.columns(2)
    
    with col1:
        price_dist = summary.get('price_distribution', {})
        if price_dist.get('categories'):
            categories = price_dist['categories']
            
            fig = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                title="Price Category Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        sentiment_dist = summary.get('sentiment_distribution', {})
        if sentiment_dist.get('distribution'):
            dist = sentiment_dist['distribution']
            
            fig = px.pie(
                values=list(dist.values()),
                names=list(dist.keys()),
                title="Sentiment Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)


def render_brand_comparison_page():
    """Render brand comparison page"""
    st.markdown('<h1 class="main-header">Brand Comparison</h1>', unsafe_allow_html=True)
    
    # Get all brands
    brands_data = fetch_api_data("/brands")
    if not brands_data:
        st.error("Unable to load brand data")
        return
    
    # Brand selector
    brand_names = [brand['brand'] for brand in brands_data]
    selected_brands = st.multiselect(
        "Select brands to compare",
        brand_names,
        default=brand_names[:3] if len(brand_names) >= 3 else brand_names
    )
    
    if len(selected_brands) < 2:
        st.warning("Please select at least 2 brands to compare")
        return
    
    # Fetch comparison data
    comparison = fetch_api_data("/compare", params={"brands": selected_brands})
    if not comparison:
        st.error("Unable to fetch comparison data")
        return
    
    # Comparison metrics
    metrics = comparison.get('metrics', {})
    
    # Create comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Competitive scores
        if 'competitive_score' in metrics:
            scores = metrics['competitive_score']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(scores.keys()),
                    y=list(scores.values()),
                    marker_color='lightblue'
                )
            ])
            
            fig.update_layout(
                title="Competitive Score Comparison",
                xaxis_title="Brand",
                yaxis_title="Score"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Value scores
        if 'value_score' in metrics:
            scores = metrics['value_score']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(scores.keys()),
                    y=list(scores.values()),
                    marker_color='lightgreen'
                )
            ])
            
            fig.update_layout(
                title="Value Score Comparison",
                xaxis_title="Brand",
                yaxis_title="Score"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Detailed comparison table
    st.subheader("Detailed Comparison")
    
    comparison_data = []
    for brand in selected_brands:
        brand_details = fetch_api_data(f"/brands/{brand}")
        if brand_details:
            metrics = brand_details.get('metrics', {})
            comparison_data.append({
                'Brand': brand,
                'Competitive Rank': brand_details.get('summary', {}).get('competitive_rank', 0),
                'Competitive Score': brand_details.get('summary', {}).get('competitive_score', 0),
                'Value Score': brand_details.get('summary', {}).get('value_score', 0),
                'Avg Price': f"${metrics.get('avg_price', 0):.2f}",
                'Avg Rating': f"{metrics.get('avg_rating', 0):.1f}",
                'Total Products': metrics.get('total_products', 0),
                'Total Reviews': metrics.get('total_reviews', 0)
            })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
    
    # Insights
    rankings = comparison.get('ranking', {})
    if rankings:
        st.subheader("Rankings Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'competitive' in rankings:
                st.write("**Competitive Ranking:**")
                for i, brand in enumerate(rankings['competitive'][:3], 1):
                    st.write(f"{i}. {brand}")
        
        with col2:
            if 'value' in rankings:
                st.write("**Value Ranking:**")
                for i, brand in enumerate(rankings['value'][:3], 1):
                    st.write(f"{i}. {brand}")
        
        with col3:
            if 'price' in rankings:
                st.write("**Price Ranking (Low to High):**")
                for i, brand in enumerate(rankings['price'][:3], 1):
                    st.write(f"{i}. {brand}")


def render_products_page():
    """Render products page"""
    st.markdown('<h1 class="main-header">Product Analysis</h1>', unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        brands_data = fetch_api_data("/brands")
        brand_names = [brand['brand'] for brand in brands_data] if brands_data else []
        selected_brand = st.selectbox("Brand", ["All"] + brand_names)
    
    with col2:
        min_price = st.number_input("Min Price", min_value=0, value=0, step=100)
    
    with col3:
        max_price = st.number_input("Max Price", min_value=0, value=10000, step=100)
    
    with col4:
        min_rating = st.selectbox("Min Rating", [0, 1, 2, 3, 4, 5], index=0)
    
    # Fetch products
    params = {
        "limit": 50,
        "min_price": min_price if min_price > 0 else None,
        "max_price": max_price if max_price > 0 else None,
        "min_rating": min_rating if min_rating > 0 else None
    }
    
    if selected_brand != "All":
        params["brand"] = selected_brand
    
    products_response = fetch_api_data("/products", params=params)
    
    if not products_response:
        st.error("Unable to load products")
        return
    
    products = products_response.get('products', [])
    total_count = products_response.get('total_count', 0)
    
    st.info(f"Showing {len(products)} of {total_count} products")
    
    if products:
        # Convert to DataFrame
        products_df = pd.DataFrame(products)
        
        # Display products
        for _, product in products_df.iterrows():
            with st.expander(f"{product['title']} - {product['brand']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Price:** ${product['price']:.2f}")
                    st.write(f"**Rating:** {product['rating']:.1f}/5")
                    st.write(f"**Reviews:** {product['review_count']}")
                
                with col2:
                    st.write(f"**Sentiment Score:** {product['sentiment_score']:.2f}")
                    if product['themes']:
                        st.write("**Themes:**")
                        for theme in product['themes'][:5]:
                            st.write(f"- {theme}")
        
        # Price vs Rating scatter plot
        if len(products_df) > 1:
            fig = px.scatter(
                products_df,
                x='price',
                y='rating',
                color='brand',
                size='review_count',
                hover_data=['title'],
                title="Price vs Rating Analysis"
            )
            
            fig.update_layout(
                xaxis_title="Price ($)",
                yaxis_title="Rating"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No products found matching the criteria")


def render_reviews_page():
    """Render reviews page"""
    st.markdown('<h1 class="main-header">Customer Reviews</h1>', unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        brands_data = fetch_api_data("/brands")
        brand_names = [brand['brand'] for brand in brands_data] if brands_data else []
        selected_brand = st.selectbox("Brand", ["All"] + brand_names)
    
    with col2:
        selected_sentiment = st.selectbox("Sentiment", ["All", "Positive", "Negative", "Neutral"])
    
    with col3:
        themes_response = fetch_api_data("/stats")
        themes = themes_response.get('themes', {}).get('top_themes', [])
        theme_names = [theme['theme'] for theme in themes] if themes else []
        selected_theme = st.selectbox("Theme", ["All"] + theme_names)
    
    with col4:
        min_rating = st.selectbox("Min Rating", [0, 1, 2, 3, 4, 5], index=0)
    
    # Fetch reviews
    params = {
        "limit": 20,
        "min_rating": min_rating if min_rating > 0 else None
    }
    
    if selected_brand != "All":
        params["brand"] = selected_brand
    
    if selected_sentiment != "All":
        params["sentiment"] = selected_sentiment
    
    if selected_theme != "All":
        params["theme"] = selected_theme
    
    reviews_response = fetch_api_data("/reviews", params=params)
    
    if not reviews_response:
        st.error("Unable to load reviews")
        return
    
    reviews = reviews_response.get('reviews', [])
    total_count = reviews_response.get('total_count', 0)
    
    st.info(f"Showing {len(reviews)} of {total_count} reviews")
    
    if reviews:
        for review in reviews:
            sentiment_color = {
                'Positive': 'green',
                'Negative': 'red',
                'Neutral': 'orange'
            }.get(review['sentiment_label'], 'gray')
            
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0;">
                <h4 style="margin: 0; color: {sentiment_color};">{review['title']}</h4>
                <p><strong>Rating:</strong> {review['rating']}/5 | 
                   <strong>Sentiment:</strong> {review['sentiment_label']} ({review['sentiment_score']:.2f})</p>
                <p>{review['text']}</p>
                {f"<p><strong>Themes:</strong> {', '.join(review['themes'])}</p>" if review['themes'] else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No reviews found matching the criteria")


def render_insights_page():
    """Render insights page"""
    st.markdown('<h1 class="main-header">AI Insights</h1>', unsafe_allow_html=True)
    
    # Fetch insights
    insights_response = fetch_api_data("/insights", params={"limit": 30})
    
    if not insights_response:
        st.error("Unable to load insights")
        return
    
    insights = insights_response
    
    if not insights:
        st.info("No insights available")
        return
    
    # Filter by type
    insight_types = list(set(insight['type'] for insight in insights))
    selected_type = st.selectbox("Filter by Insight Type", ["All"] + insight_types)
    
    filtered_insights = insights if selected_type == "All" else [
        insight for insight in insights if insight['type'] == selected_type
    ]
    
    # Sort by priority
    filtered_insights.sort(key=lambda x: x.get('priority', 0), reverse=True)
    
    # Display insights
    for insight in filtered_insights:
        priority_color = {
            10: 'red',
            9: 'orange',
            8: 'yellow',
            7: 'blue',
            6: 'green',
            5: 'gray'
        }.get(insight.get('priority', 5), 'gray')
        
        st.markdown(f"""
        <div class="insight-card">
            <h4>{insight.get('title', 'Untitled')}</h4>
            <p><strong>Type:</strong> {insight.get('type', 'Unknown')} | 
               <strong>Priority:</strong> <span style="color: {priority_color}">{insight.get('priority', 5)}/10</span>
               {f"| <strong>Brand:</strong> {insight.get('brand')}" if insight.get('brand') else ""}</p>
            <p>{insight.get('description', 'No description')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Insights summary
    st.subheader("Insights Summary")
    
    # Count by type
    type_counts = {}
    for insight in insights:
        insight_type = insight.get('type', 'unknown')
        type_counts[insight_type] = type_counts.get(insight_type, 0) + 1
    
    if type_counts:
        fig = px.pie(
            values=list(type_counts.values()),
            names=list(type_counts.keys()),
            title="Insights by Type"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_search_page():
    """Render search page"""
    st.markdown('<h1 class="main-header">Product Search</h1>', unsafe_allow_html=True)
    
    # Search input
    query = st.text_input("Search products by title or brand", placeholder="Enter search terms...")
    
    if query:
        search_results = fetch_api_data("/search", params={"query": query, "limit": 20})
        
        if search_results:
            results = search_results.get('results', [])
            total_count = search_results.get('total_count', 0)
            
            st.info(f"Found {total_count} products matching '{query}'")
            
            if results:
                for product in results:
                    with st.expander(f"{product['title']} - {product['brand']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Price:** ${product['price']:.2f}")
                            st.write(f"**Rating:** {product['rating']:.1f}/5")
                            st.write(f"**Reviews:** {product['review_count']}")
                        
                        with col2:
                            st.write(f"**Product ID:** {product['product_id']}")
            else:
                st.info("No products found")
        else:
            st.error("Search failed")


def main():
    """Main dashboard function"""
    # Sidebar navigation
    st.sidebar.title("LuggageIQ Navigation")
    
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Overview", "Brand Comparison", "Products", "Reviews", "Insights", "Search"]
    )
    
    # API Status
    with st.sidebar:
        st.subheader("API Status")
        try:
            health = fetch_api_data("/health")
            if health:
                st.success("API Connected")
                st.write(f"Service: {health.get('service', 'Unknown')}")
                st.write(f"Version: {health.get('version', 'Unknown')}")
        except:
            st.error("API Disconnected")
            st.write("Please start the backend server")
    
    # Load data based on page
    if page == "Overview":
        summary = load_data()
        render_overview_page(summary)
    elif page == "Brand Comparison":
        render_brand_comparison_page()
    elif page == "Products":
        render_products_page()
    elif page == "Reviews":
        render_reviews_page()
    elif page == "Insights":
        render_insights_page()
    elif page == "Search":
        render_search_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "LuggageIQ is an AI-powered competitive intelligence dashboard for Amazon luggage brands. "
        "It provides insights on pricing, sentiment, themes, and market positioning."
    )


if __name__ == "__main__":
    main()
