"""
Enhanced LuggageIQ Dashboard with improved UX and new visualizations
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from typing import Dict, List, Optional
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger('enhanced_dashboard')

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Custom CSS for enhanced UI
def load_custom_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .insight-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .brand-highlight {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stSelectbox > div > div {
        background: #f0f2f6;
        border-radius: 5px;
    }
    
    .dataframe {
        font-size: 14px;
    }
    
    .plot-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

def fetch_api_data(endpoint: str, params: Dict = None) -> Dict:
    """Fetch data from API with error handling"""
    try:
        if endpoint == '/health':
            url = f"http://localhost:8000/health"
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

def create_summary_cards(data: Dict) -> None:
    """Create enhanced summary cards"""
    if not data:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>{}</h3>
            <p>Total Brands</p>
            <h2>{}</h2>
        </div>
        """.format(data.get('overview', {}).get('total_brands', 0), 
                 data.get('overview', {}).get('total_brands', 0)), 
                 unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>{}</h3>
            <p>Total Products</p>
            <h2>{}</h2>
        </div>
        """.format(data.get('overview', {}).get('total_products', 0),
                 data.get('overview', {}).get('total_products', 0)), 
                 unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>{}</h3>
            <p>Total Reviews</p>
            <h2>{}</h2>
        </div>
        """.format(data.get('overview', {}).get('total_reviews', 0),
                 data.get('overview', {}).get('total_reviews', 0)), 
                 unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>{:.2f}</h3>
            <p>Avg Rating</p>
            <h2>{:.2f}</h2>
        </div>
        """.format(data.get('overview', {}).get('avg_rating', 0),
                 data.get('overview', {}).get('avg_rating', 0)), 
                 unsafe_allow_html=True)

def create_sentiment_vs_price_scatter(products_df: pd.DataFrame, reviews_df: pd.DataFrame) -> None:
    """Create sentiment vs price scatter plot"""
    if products_df.empty or reviews_df.empty:
        st.warning("No data available for sentiment vs price analysis")
        return
    
    # Merge data
    merged_df = products_df.merge(reviews_df.groupby('product_id')['sentiment_score'].mean().reset_index(), 
                                 on='product_id', how='left')
    
    if merged_df.empty:
        st.warning("No merged data available")
        return
    
    fig = px.scatter(merged_df, 
                     x='price', 
                     y='sentiment_score',
                     color='brand',
                     size='review_count',
                     hover_data=['title', 'rating'],
                     title='Sentiment Score vs Price Analysis',
                     labels={
                         'price': 'Price ($)',
                         'sentiment_score': 'Average Sentiment Score',
                         'review_count': 'Review Count'
                     })
    
    fig.update_layout(
        xaxis_title="Price ($)",
        yaxis_title="Sentiment Score",
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_discount_vs_rating_chart(products_df: pd.DataFrame) -> None:
    """Create discount vs rating chart"""
    if products_df.empty:
        st.warning("No data available for discount vs rating analysis")
        return
    
    fig = px.scatter(products_df,
                     x='discount_pct',
                     y='rating',
                     color='brand',
                     size='review_count',
                     hover_data=['title', 'price'],
                     title='Discount Percentage vs Rating Analysis',
                     labels={
                         'discount_pct': 'Discount (%)',
                         'rating': 'Rating',
                         'review_count': 'Review Count'
                     })
    
    # Add trend line
    fig.add_trace(go.Scatter(
        x=products_df['discount_pct'],
        y=products_df['rating'],
        mode='markers',
        name='Data Points',
        marker=dict(size=8, opacity=0.6)
    ))
    
    fig.update_layout(
        xaxis_title="Discount Percentage (%)",
        yaxis_title="Rating",
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_theme_frequency_chart(theme_stats: Dict) -> None:
    """Create theme frequency bar chart"""
    if not theme_stats or 'overall_frequency' not in theme_stats:
        st.warning("No theme data available")
        return
    
    theme_freq = theme_stats['overall_frequency']
    if not theme_freq:
        st.warning("No theme frequency data available")
        return
    
    # Sort by frequency
    sorted_themes = sorted(theme_freq.items(), key=lambda x: x[1], reverse=True)
    themes, frequencies = zip(*sorted_themes)
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(themes),
            y=list(frequencies),
            marker_color='rgb(55, 83, 109)',
            text=list(frequencies),
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title='Theme Frequency Analysis',
        xaxis_title='Themes',
        yaxis_title='Frequency',
        height=500,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_value_for_money_analysis(products_df: pd.DataFrame, reviews_df: pd.DataFrame) -> None:
    """Create value for money analysis"""
    if products_df.empty or reviews_df.empty:
        st.warning("No data available for value analysis")
        return
    
    # Calculate value scores
    brand_value = []
    for brand in products_df['brand'].unique():
        brand_products = products_df[products_df['brand'] == brand]
        brand_reviews = reviews_df[reviews_df['product_id'].isin(brand_products['product_id'])]
        
        if not brand_reviews.empty:
            avg_price = brand_products['price'].mean()
            avg_rating = brand_products['rating'].mean()
            avg_sentiment = brand_reviews['sentiment_score'].mean()
            
            # Calculate value score
            min_price = products_df['price'].min()
            max_price = products_df['price'].max()
            normalized_price = (avg_price - min_price) / (max_price - min_price)
            value_score = (avg_rating / 5) / (normalized_price + 0.1)
            
            brand_value.append({
                'brand': brand,
                'value_score': value_score,
                'avg_price': avg_price,
                'avg_rating': avg_rating,
                'avg_sentiment': avg_sentiment
            })
    
    if not brand_value:
        st.warning("No brand value data available")
        return
    
    value_df = pd.DataFrame(brand_value)
    value_df = value_df.sort_values('value_score', ascending=False)
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=value_df['brand'],
            y=value_df['value_score'],
            marker_color='rgb(55, 83, 109)',
            text=[f"{score:.2f}" for score in value_df['value_score']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title='Value for Money Analysis by Brand',
        xaxis_title='Brand',
        yaxis_title='Value Score',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Create detailed table
    st.subheader("Value for Money Details")
    value_df_display = value_df.round(2)
    value_df_display = value_df_display.rename(columns={
        'brand': 'Brand',
        'value_score': 'Value Score',
        'avg_price': 'Avg Price ($)',
        'avg_rating': 'Avg Rating',
        'avg_sentiment': 'Avg Sentiment'
    })
    st.dataframe(value_df_display, use_container_width=True)

def create_enhanced_brand_comparison(brands_data: List[Dict]) -> None:
    """Create enhanced brand comparison visualization"""
    if not brands_data:
        st.warning("No brand data available")
        return
    
    brands_df = pd.DataFrame(brands_data)
    
    # Create subplots for comprehensive comparison
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Average Price', 'Average Rating', 'Total Products', 'Average Sentiment'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Price comparison
    fig.add_trace(
        go.Bar(x=brands_df['brand'], y=brands_df['avg_price'], name='Avg Price'),
        row=1, col=1
    )
    
    # Rating comparison
    fig.add_trace(
        go.Bar(x=brands_df['brand'], y=brands_df['avg_rating'], name='Avg Rating'),
        row=1, col=2
    )
    
    # Product count comparison
    fig.add_trace(
        go.Bar(x=brands_df['brand'], y=brands_df['total_products'], name='Total Products'),
        row=2, col=1
    )
    
    # Sentiment comparison
    fig.add_trace(
        go.Bar(x=brands_df['brand'], y=brands_df['avg_sentiment'], name='Avg Sentiment'),
        row=2, col=2
    )
    
    fig.update_layout(
        title_text="Comprehensive Brand Comparison",
        showlegend=False,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_anomaly_detection_chart(anomalies: List[Dict]) -> None:
    """Create anomaly detection visualization"""
    if not anomalies:
        st.info("No anomalies detected")
        return
    
    st.subheader("Detected Anomalies")
    
    for anomaly in anomalies:
        with st.expander(f"Anomaly: {anomaly.get('type', 'Unknown')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {anomaly.get('type', 'Unknown')}")
                st.write(f"**Severity:** {anomaly.get('severity', 'Unknown')}")
                st.write(f"**Product ID:** {anomaly.get('product_id', 'Unknown')}")
            
            with col2:
                st.write(f"**Brand:** {anomaly.get('brand', 'Unknown')}")
                st.write(f"**Rating:** {anomaly.get('rating', 'N/A')}")
                st.write(f"**Sentiment:** {anomaly.get('sentiment_score', 'N/A')}")
            
            st.write(f"**Description:** {anomaly.get('description', 'No description available')}")

def enhanced_overview_page():
    """Enhanced overview page with new visualizations"""
    st.markdown("""
    <div class="main-header">
        <h1>Enhanced LuggageIQ Dashboard</h1>
        <p>Advanced Competitive Intelligence for Amazon India Luggage Brands</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch data
    analysis_data = fetch_api_data("/analysis/summary")
    brands_data = fetch_api_data("/brands")
    products_data = fetch_api_data("/products")
    reviews_data = fetch_api_data("/reviews")
    
    # Create summary cards
    if analysis_data:
        create_summary_cards(analysis_data)
    
    # Key insights section
    st.subheader("Key Insights")
    insights_data = fetch_api_data("/insights")
    
    if insights_data:
        for insight in insights_data[:3]:  # Show top 3 insights
            st.markdown(f"""
            <div class="insight-card">
                <h4>{insight.get('title', 'Untitled')}</h4>
                <p>{insight.get('description', 'No description available')}</p>
                <small>Priority: {insight.get('priority', 'N/A')}/10 | Confidence: {insight.get('confidence', 0):.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # New visualizations
    st.subheader("Advanced Analytics")
    
    # Get data for visualizations
    products_df = pd.DataFrame()
    reviews_df = pd.DataFrame()
    
    if products_data and 'products' in products_data:
        products_df = pd.DataFrame(products_data['products'])
    
    if reviews_data and 'reviews' in reviews_data:
        reviews_df = pd.DataFrame(reviews_data['reviews'])
    
    # Create visualization tabs
    viz_tabs = st.tabs(["Sentiment vs Price", "Discount vs Rating", "Theme Analysis", "Value for Money"])
    
    with viz_tabs[0]:
        create_sentiment_vs_price_scatter(products_df, reviews_df)
    
    with viz_tabs[1]:
        create_discount_vs_rating_chart(products_df)
    
    with viz_tabs[2]:
        theme_stats = fetch_api_data("/themes") if hasattr(fetch_api_data("/themes"), 'get') else {}
        create_theme_frequency_chart(theme_stats)
    
    with viz_tabs[3]:
        create_value_for_money_analysis(products_df, reviews_df)

def enhanced_brand_comparison_page():
    """Enhanced brand comparison page"""
    st.markdown("""
    <div class="main-header">
        <h1>Brand Comparison Analysis</h1>
        <p>Comprehensive competitive analysis across multiple dimensions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Brand selection
    brands_data = fetch_api_data("/brands")
    if not brands_data:
        st.error("Unable to load brand data")
        return
    
    brand_names = [brand['brand'] for brand in brands_data]
    selected_brands = st.multiselect("Select brands to compare", brand_names, default=brand_names[:3])
    
    if not selected_brands:
        st.warning("Please select at least one brand to compare")
        return
    
    # Fetch comparison data
    comparison_data = fetch_api_data("/compare", {"brands": selected_brands})
    
    if comparison_data:
        st.subheader("Comprehensive Comparison")
        create_enhanced_brand_comparison(comparison_data.get('top_brands', []))
        
        # Detailed metrics table
        st.subheader("Detailed Metrics")
        metrics = comparison_data.get('metrics', {})
        
        if metrics:
            comparison_df = pd.DataFrame({
                'Brand': selected_brands,
                'Competitive Score': [metrics.get('competitive_score', {}).get(brand, 0) for brand in selected_brands],
                'Value Score': [metrics.get('value_score', {}).get(brand, 0) for brand in selected_brands],
                'Avg Price': [metrics.get('avg_price', {}).get(brand, 0) for brand in selected_brands],
                'Avg Rating': [metrics.get('avg_rating', {}).get(brand, 0) for brand in selected_brands],
                'Total Products': [metrics.get('total_products', {}).get(brand, 0) for brand in selected_brands],
                'Avg Sentiment': [metrics.get('avg_sentiment', {}).get(brand, 0) for brand in selected_brands]
            })
            
            st.dataframe(comparison_df.round(2), use_container_width=True)

def enhanced_product_drilldown_page():
    """Enhanced product drilldown page"""
    st.markdown("""
    <div class="main-header">
        <h1>Product Drilldown Analysis</h1>
        <p>Detailed analysis of individual products</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Product selection
    products_data = fetch_api_data("/products")
    if not products_data or 'products' not in products_data:
        st.error("Unable to load product data")
        return
    
    products_df = pd.DataFrame(products_data['products'])
    
    # Product selector
    product_options = [f"{row['title']} ({row['brand']})" for _, row in products_df.iterrows()]
    selected_product_index = st.selectbox("Select a product", range(len(product_options)), format_func=lambda x: product_options[x])
    
    selected_product = products_df.iloc[selected_product_index]
    
    # Product details
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Price", f"${selected_product['price']:.0f}")
        st.metric("Rating", f"{selected_product['rating']:.1f}/5")
    
    with col2:
        st.metric("Brand", selected_product['brand'])
        st.metric("Reviews", selected_product['review_count'])
    
    with col3:
        st.metric("Discount", f"{selected_product.get('discount_pct', 0):.1f}%")
        # Calculate value score
        value_score = (selected_product['rating'] / 5) / (selected_product['price'] / 5000 + 0.1)
        st.metric("Value Score", f"{value_score:.2f}")
    
    # Product reviews analysis
    st.subheader("Review Analysis")
    reviews_data = fetch_api_data("/reviews", {"product_id": selected_product['product_id']})
    
    if reviews_data and 'reviews' in reviews_data:
        reviews_df = pd.DataFrame(reviews_data['reviews'])
        
        if not reviews_df.empty:
            # Sentiment distribution
            col1, col2 = st.columns(2)
            
            with col1:
                sentiment_dist = reviews_df['sentiment_label'].value_counts()
                fig = px.pie(values=sentiment_dist.values, names=sentiment_dist.index, title="Sentiment Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                rating_dist = reviews_df['rating'].value_counts().sort_index()
                fig = px.bar(x=rating_dist.index, y=rating_dist.values, title="Rating Distribution")
                fig.update_layout(xaxis_title="Rating", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
            
            # Theme analysis
            if 'themes' in reviews_df.columns:
                all_themes = []
                for themes in reviews_df['themes']:
                    if isinstance(themes, list):
                        all_themes.extend(themes)
                
                if all_themes:
                    theme_counts = pd.Series(all_themes).value_counts().head(10)
                    fig = px.bar(x=theme_counts.index, y=theme_counts.values, title="Top Themes")
                    fig.update_layout(xaxis_title="Theme", yaxis_title="Count")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Sample reviews
            st.subheader("Sample Reviews")
            for _, review in reviews_df.head(5).iterrows():
                with st.expander(f"Rating: {review['rating']}/5 - {review.get('sentiment_label', 'Unknown')}"):
                    st.write(f"**{review.get('title', 'No title')}**")
                    st.write(review.get('text', 'No text available'))
                    if 'themes' in review and review['themes']:
                        st.write(f"**Themes:** {', '.join(review['themes'])}")

def enhanced_insights_page():
    """Enhanced insights page"""
    st.markdown("""
    <div class="main-header">
        <h1>AI-Powered Insights</h1>
        <p>Advanced business intelligence and recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch insights
    insights_data = fetch_api_data("/insights")
    
    if not insights_data:
        st.error("Unable to load insights data")
        return
    
    # Filter insights
    insight_types = list(set(insight.get('type', 'unknown') for insight in insights_data))
    selected_type = st.selectbox("Filter by insight type", ["All"] + insight_types)
    
    filtered_insights = insights_data if selected_type == "All" else [i for i in insights_data if i.get('type') == selected_type]
    
    # Sort by priority
    filtered_insights.sort(key=lambda x: (x.get('priority', 0) * x.get('confidence', 0)), reverse=True)
    
    # Display insights
    for insight in filtered_insights:
        priority_color = "red" if insight.get('priority', 0) >= 8 else "orange" if insight.get('priority', 0) >= 6 else "green"
        
        st.markdown(f"""
        <div class="insight-card">
            <h4>{insight.get('title', 'Untitled')}</h4>
            <p>{insight.get('description', 'No description available')}</p>
            <p><strong>Type:</strong> {insight.get('type', 'Unknown')} | 
               <strong>Priority:</strong> <span style="color: {priority_color}">{insight.get('priority', 0)}/10</span> | 
               <strong>Confidence:</strong> {insight.get('confidence', 0):.1f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendations
        if insight.get('recommendations'):
            st.write("**Recommendations:**")
            for rec in insight.get('recommendations', []):
                st.write(f"  - {rec}")
        
        # Evidence
        if insight.get('evidence'):
            with st.expander("Evidence"):
                for evidence in insight.get('evidence', []):
                    st.write(f"  - {evidence}")
        
        st.markdown("---")

def main():
    """Main enhanced dashboard application"""
    load_custom_css()
    
    # Sidebar navigation
    st.sidebar.title("LuggageIQ Enhanced")
    page = st.sidebar.selectbox("Navigate", [
        "Overview", "Brand Comparison", "Product Drilldown", "Insights", "Anomaly Detection"
    ])
    
    # Health check
    health_data = fetch_api_data("/health")
    if health_data and health_data.get('status') == 'healthy':
        st.sidebar.success("API Status: Healthy")
    else:
        st.sidebar.error("API Status: Unhealthy")
    
    # Render selected page
    if page == "Overview":
        enhanced_overview_page()
    elif page == "Brand Comparison":
        enhanced_brand_comparison_page()
    elif page == "Product Drilldown":
        enhanced_product_drilldown_page()
    elif page == "Insights":
        enhanced_insights_page()
    elif page == "Anomaly Detection":
        st.markdown("""
        <div class="main-header">
            <h1>Anomaly Detection</h1>
            <p>Identify unusual patterns and potential issues</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Fetch anomaly data (would need to be implemented in API)
        anomalies = []  # Placeholder
        create_anomaly_detection_chart(anomalies)

if __name__ == "__main__":
    main()
