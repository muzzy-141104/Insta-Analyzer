import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import glob
from main import InstagramAnalyticsScraper
import time

# Page configuration
st.set_page_config(
    page_title="Instagram Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'scraper' not in st.session_state:
    st.session_state.scraper = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False

# Custom CSS for better styling
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .stat-container {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 20px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

def get_latest_analytics_files():
    """Get list of latest analytics JSON files"""
    analytics_files = glob.glob(os.path.join(".", "*_analytics_*.json"))
    return sorted(analytics_files, key=os.path.getctime, reverse=True)

def load_analytics_data(filepath):
    """Load analytics data from JSON file"""
    try:
        # Try UTF-8 encoding first
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        try:
            # Try UTF-8 with errors ignored
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return json.load(f)
        except Exception as e:
            try:
                # Try latin-1 encoding as fallback
                with open(filepath, 'r', encoding='latin-1') as f:
                    return json.load(f)
            except Exception as e2:
                st.error(f"Error loading file: {e2}")
                return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def format_large_number(num):
    """Format large numbers with K, M, B suffixes"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    else:
        return str(int(num))

def display_profile_section(profile_info):
    """Display profile information"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if profile_info.get('profile_pic_url'):
            st.image(profile_info['profile_pic_url'], width=150)
    
    with col2:
        st.title(f"@{profile_info.get('username', 'Unknown')}")
        st.write(f"**{profile_info.get('display_name', 'Unknown')}**")
        
        badges = []
        if profile_info.get('is_verified'):
            badges.append("✅ Verified")
        if profile_info.get('is_business'):
            badges.append("💼 Business Account")
        
        if badges:
            st.write(" | ".join(badges))
        
        if profile_info.get('bio'):
            st.write(f"📝 {profile_info['bio'][:100]}")
        
        if profile_info.get('external_url'):
            st.write(f"🔗 [External Link]({profile_info['external_url']})")

def display_engagement_metrics(metrics):
    """Display engagement metrics in a beautiful layout"""
    st.markdown("### 📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👥 Followers",
            format_large_number(metrics.get('followers', 0))
        )
    
    with col2:
        st.metric(
            "📱 Following",
            format_large_number(metrics.get('following', 0))
        )
    
    with col3:
        st.metric(
            "📸 Total Posts",
            format_large_number(metrics.get('total_posts', 0))
        )
    
    with col4:
        st.metric(
            "📅 Posts/Week",
            round(metrics.get('posts_per_week', 0), 2)
        )
    
    st.markdown("---")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            "❤️ Avg Likes",
            format_large_number(metrics.get('average_likes', 0))
        )
    
    with col6:
        st.metric(
            "💬 Avg Comments",
            format_large_number(metrics.get('average_comments', 0))
        )
    
    with col7:
        st.metric(
            "👁️ Avg Views",
            format_large_number(metrics.get('average_views', 0))
        )
    
    with col8:
        st.metric(
            "💥 Engagement Rate",
            f"{metrics.get('engagement_rate', 0):.2f}%"
        )

def display_content_analysis(content_analysis):
    """Display content type distribution and hashtags"""
    st.markdown("### 📈 Content Analysis")
    
    col1, col2 = st.columns(2)
    
    # Content Type Distribution
    with col1:
        content_dist = content_analysis.get('content_type_distribution', {})
        if content_dist:
            fig_pie = px.pie(
                values=list(content_dist.values()),
                names=list(content_dist.keys()),
                title="Content Type Distribution",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Top Hashtags
    with col2:
        top_hashtags = content_analysis.get('top_hashtags', [])[:10]
        if top_hashtags:
            hashtag_df = pd.DataFrame(top_hashtags)
            fig_bar = px.bar(
                hashtag_df,
                x='count',
                y='tag',
                orientation='h',
                title="Top 10 Hashtags",
                color='count',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

def display_engagement_analysis(engagement_analysis):
    """Display engagement analysis"""
    st.markdown("### 💡 Engagement Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metrics_data = {
            'Metric': ['Avg Likes', 'Avg Comments', 'Avg Engagement'],
            'Value': [
                engagement_analysis.get('avg_likes', 0),
                engagement_analysis.get('avg_comments', 0),
                engagement_analysis.get('avg_engagement_per_post', 0)
            ]
        }
        metrics_df = pd.DataFrame(metrics_data)
        
        fig_bar = px.bar(
            metrics_df,
            x='Metric',
            y='Value',
            title="Average Engagement Metrics",
            color='Value',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        engagement_stats = {
            'Stat': [
                'Engagement Rate',
                'Median Engagement',
                'Max Engagement',
                'Viral Posts'
            ],
            'Value': [
                f"{engagement_analysis.get('engagement_rate_percent', 0):.2f}%",
                format_large_number(engagement_analysis.get('median_engagement', 0)),
                format_large_number(engagement_analysis.get('max_engagement', 0)),
                engagement_analysis.get('viral_posts_count', 0)
            ]
        }
        st.info(f"""
        **Engagement Stats:**
        - Engagement Rate: {engagement_stats['Value'][0]}
        - Median Engagement: {engagement_stats['Value'][1]}
        - Max Engagement: {engagement_stats['Value'][2]}
        - Viral Posts: {engagement_stats['Value'][3]}
        """)

def display_top_posts(top_posts):
    """Display top performing posts"""
    st.markdown("### 🏆 Top Performing Posts")
    
    if not top_posts:
        st.info("No post data available")
        return
    
    for idx, post in enumerate(top_posts[:5], 1):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**#{idx} - {post.get('type', 'Unknown')}**")
            st.write(f"Engagement: {format_large_number(post.get('engagement', 0))}")
            st.write(f"Post Link: {post.get('shortcode', 'N/A')}")
        
        with col2:
            st.metric("", format_large_number(post.get('engagement', 0)))
        
        st.divider()

def display_audience_analysis(audience_analysis):
    """Display audience demographics"""
    st.markdown("### 👥 Audience Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gender_dist = audience_analysis.get('gender_distribution', {})
        if gender_dist:
            fig_pie = px.pie(
                values=list(gender_dist.values()),
                names=list(gender_dist.keys()),
                title="Gender Distribution",
                color_discrete_sequence=['#FF6B9D', '#4A90E2']
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        age_dist = audience_analysis.get('age_distribution', {})
        if age_dist:
            age_df = pd.DataFrame({
                'Age Group': list(age_dist.keys()),
                'Count': list(age_dist.values())
            })
            fig_bar = px.bar(
                age_df,
                x='Age Group',
                y='Count',
                title="Age Distribution",
                color='Count',
                color_continuous_scale='Purples'
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)

def display_brand_collaborations(brand_collabs, total_brand_posts):
    """Display brand collaborations"""
    st.markdown("### 💼 Brand Collaborations")
    
    if not brand_collabs:
        st.info("No brand collaborations detected")
        return
    
    st.metric("Total Brand Posts", total_brand_posts)
    
    st.markdown("#### Recent Brand Collaborations")
    for idx, collab in enumerate(brand_collabs[:10], 1):
        with st.expander(f"📌 Post {idx} - {collab.get('date', 'Unknown')}"):
            st.write(f"**Date:** {collab.get('date', 'N/A')}")
            st.write(f"**Caption:** {collab.get('caption_snippet', 'N/A')[:200]}...")
            st.write(f"**Link:** [{collab.get('post_url', 'N/A')}]({collab.get('post_url', '#')})")

def display_engagement_timeline(timeline_data):
    """Display engagement timeline chart"""
    st.markdown("### 📈 Engagement Timeline")
    
    if not timeline_data:
        st.info("No timeline data available")
        return
    
    timeline_df = pd.DataFrame(timeline_data)
    
    # Create dual-axis chart
    fig = go.Figure()
    
    # Add likes line
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['likes'],
        mode='lines+markers',
        name='Likes',
        line=dict(color='#E1306C', width=3),
        marker=dict(size=8)
    ))
    
    # Add comments line
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['comments'],
        mode='lines+markers',
        name='Comments',
        line=dict(color='#5B51D8', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Engagement Over Time",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Likes", side='left'),
        yaxis2=dict(title="Comments", side='right', overlaying='y'),
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Engagement rate chart
    fig_rate = px.line(
        timeline_df,
        x='date',
        y='engagement_rate',
        title='Engagement Rate Over Time',
        markers=True,
        line_shape='spline'
    )
    fig_rate.update_traces(line=dict(color='#00D9FF', width=3))
    fig_rate.update_layout(height=400)
    st.plotly_chart(fig_rate, use_container_width=True)

def display_trend_analysis(trend_analysis):
    """Display trend analysis section"""
    st.markdown("### 📊 Trend Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Viral Posts",
            trend_analysis.get('viral_posts_count', 0)
        )
    
    with col2:
        st.metric(
            "Viral Percentage",
            f"{trend_analysis.get('viral_video_percentage', 0):.2f}%"
        )
    
    with col3:
        total_posts = len(trend_analysis.get('top_performing_posts', []))
        st.metric(
            "Posts Analyzed",
            total_posts
        )
    
    st.markdown("---")
    
    # Display top performing posts with full details
    st.markdown("#### 🏆 Top Performing Posts")
    
    top_posts = trend_analysis.get('top_performing_posts', [])[:5]
    
    for idx, post in enumerate(top_posts, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**#{idx} - {post.get('type', 'Unknown')} Post**")
                st.write(f"📅 Date: {post.get('date', 'N/A')}")
                st.write(f"💬 Caption: {post.get('caption', 'N/A')[:150]}...")
                
                # Show hashtags if available
                if post.get('hashtags'):
                    st.write(f"🏷️ Hashtags: {', '.join(['#' + tag for tag in post.get('hashtags', [])])}")
                
                # Show mentions if available
                if post.get('mentions'):
                    st.write(f"👤 Mentions: {', '.join(['@' + user for user in post.get('mentions', [])])}")
                
                st.markdown(f"🔗 [View Post]({post.get('url', '#')})")
            
            with col2:
                st.metric("Likes", format_large_number(post.get('likes', 0)))
                st.metric("Comments", format_large_number(post.get('comments', 0)))
                if post.get('views', 0) > 0:
                    st.metric("Views", format_large_number(post.get('views', 0)))
            
            st.divider()

def main():
    # Header
    st.markdown("""
    <div class="header">
        <h1>📊 Instagram Analytics Dashboard</h1>
        <p>Advanced Instagram Profile Analytics & Insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 📁 Options")
    
    # Add tabs for viewing/scraping
    tab_selection = st.sidebar.radio(
        "Choose Action:",
        ["📊 View Analytics", "🔍 Scrape New Profile"],
        index=0
    )
    
    # SCRAPING SECTION
    if tab_selection == "🔍 Scrape New Profile":
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔐 Login (Optional but Recommended)")
        
        with st.sidebar.expander("ℹ️ Why Login?", expanded=False):
            st.write("""
            - Avoid rate limits
            - Access more data
            - Better reliability
            - Won't get 401 errors
            """)
        
        insta_username = st.sidebar.text_input("Your Instagram Username", key="login_user")
        insta_password = st.sidebar.text_input("Your Instagram Password", type="password", key="login_pass")
        
        if st.sidebar.button("🔑 Login to Instagram"):
            if insta_username and insta_password:
                with st.spinner("Logging in..."):
                    if st.session_state.scraper is None:
                        st.session_state.scraper = InstagramAnalyticsScraper()
                    
                    if st.session_state.scraper.login(insta_username, insta_password):
                        st.session_state.logged_in = True
                        st.sidebar.success("✅ Logged in successfully!")
                    else:
                        st.sidebar.error("❌ Login failed. Check credentials.")
            else:
                st.sidebar.warning("⚠️ Please enter both username and password")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 Target Profile")
        
        target_username = st.sidebar.text_input("Instagram Username to Scrape", placeholder="e.g., cristiano")
        max_posts = st.sidebar.slider("Maximum Posts to Analyze", min_value=10, max_value=100, value=50, step=10)
        delay = st.sidebar.slider("Delay Between Posts (seconds)", min_value=1, max_value=5, value=2)
        
        if st.sidebar.button("🚀 Start Scraping", type="primary"):
            if not target_username:
                st.sidebar.error("⚠️ Please enter a username to scrape")
            else:
                st.session_state.scraping_in_progress = True
                
                # Main content area for scraping
                st.markdown(f"## 🔍 Scraping @{target_username}")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_area = st.empty()
                
                try:
                    # Initialize scraper if not done
                    if st.session_state.scraper is None:
                        st.session_state.scraper = InstagramAnalyticsScraper()
                    
                    status_text.text(f"Starting scrape for @{target_username}...")
                    
                    # Scrape the profile
                    with st.spinner(f"Scraping {max_posts} posts from @{target_username}..."):
                        analytics_data = st.session_state.scraper.scrape_profile(
                            target_username,
                            max_posts=max_posts,
                            delay_between_posts=delay
                        )
                    
                    if analytics_data:
                        # Add advanced analytics if not present
                        if 'engagement_analysis' not in analytics_data:
                            status_text.text("📊 Running advanced analytics...")
                            advanced_analytics = InstagramAnalytics()
                            
                            # Get posts data from trend_analysis if available
                            posts_data = []
                            if 'trend_analysis' in analytics_data and 'top_performing_posts' in analytics_data['trend_analysis']:
                                posts_data = analytics_data['trend_analysis']['top_performing_posts']
                            
                            if posts_data:
                                followers = analytics_data.get('engagement_metrics', {}).get('followers', 0)
                                engagement_analysis = advanced_analytics.calculate_engagement_metrics(posts_data, followers)
                                analytics_data['engagement_analysis'] = engagement_analysis
                        
                        # Save the data
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{target_username}_analytics_{timestamp}.json"
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(analytics_data, f, indent=2, default=str, ensure_ascii=False)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Scraping completed successfully!")
                        
                        st.success(f"✅ Analytics saved to: {filename}")
                        st.balloons()
                        
                        # Show quick summary
                        st.markdown("### 📊 Quick Summary")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Followers", format_large_number(analytics_data['engagement_metrics']['followers']))
                        with col2:
                            st.metric("Posts Analyzed", analytics_data['posts_analyzed'])
                        with col3:
                            st.metric("Engagement Rate", f"{analytics_data['engagement_metrics']['engagement_rate']}%")
                        
                        st.info("💡 Switch to 'View Analytics' to see the full dashboard!")
                    else:
                        st.error("❌ Scraping failed. Please check the logs and try again.")
                
                except Exception as e:
                    st.error(f"❌ Error during scraping: {str(e)}")
                    st.exception(e)
                
                finally:
                    st.session_state.scraping_in_progress = False
        
        # Show login status
        if st.session_state.logged_in:
            st.sidebar.success("✅ Logged In")
        else:
            st.sidebar.info("ℹ️ Not logged in (may encounter rate limits)")
        
        return  # Exit here when in scrape mode
    
    # VIEW ANALYTICS SECTION
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Select Profile")
    
    analytics_files = get_latest_analytics_files()
    
    if not analytics_files:
        st.error("❌ No analytics files found. Please scrape a profile first using '🔍 Scrape New Profile' option.")
        return
    
    # Extract profile names from filenames
    file_options = {
        Path(f).stem.rsplit('_analytics_', 1)[0]: f for f in analytics_files
    }
    
    selected_profile = st.sidebar.selectbox(
        "Choose a profile:",
        options=list(file_options.keys())
    )
    
    # Load selected analytics
    selected_file = file_options[selected_profile]
    data = load_analytics_data(selected_file)
    
    if not data:
        st.error("Failed to load analytics data")
        return
    
    # Display file info
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📅 File: {Path(selected_file).name}")
    
    # Extract sections
    profile_info = data.get('profile_information', {})
    engagement_metrics = data.get('engagement_metrics', {})
    content_analysis = data.get('content_analysis', {})
    engagement_analysis = data.get('engagement_analysis', {})
    audience_analysis = data.get('audience_analysis', {})
    trend_analysis = data.get('trend_analysis', {})
    
    # Display Profile Section
    display_profile_section(profile_info)
    
    st.markdown("---")
    
    # Display Engagement Metrics
    display_engagement_metrics(engagement_metrics)
    
    # Display scraping info
    st.info(f"""
    **Scraping Info:** 
    📊 Posts Analyzed: {data.get('posts_analyzed', 'N/A')} | 
    ❌ Posts Failed: {data.get('posts_failed', 0)} | 
    📅 Scraped At: {data.get('scraped_at', 'N/A')[:19]}
    """)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Content Analysis",
        "💡 Engagement Deep Dive",
        "� Trends & Timeline",
        "💼 Brand Collabs",
        "�👥 Audience",
        "📋 Summary"
    ])
    
    with tab1:
        display_content_analysis(content_analysis)
    
    with tab2:
        if engagement_analysis:
            display_engagement_analysis(engagement_analysis)
            st.divider()
            display_top_posts(engagement_analysis.get('top_performing_posts', []))
        else:
            st.info("No engagement analysis data available")
    
    with tab3:
        if trend_analysis:
            display_trend_analysis(trend_analysis)
            st.divider()
            # Display engagement timeline
            timeline_data = trend_analysis.get('engagement_timeline', [])
            if timeline_data:
                display_engagement_timeline(timeline_data)
        else:
            st.info("No trend analysis data available")
    
    with tab4:
        brand_collabs = content_analysis.get('brand_collaborations', [])
        total_brand_posts = content_analysis.get('total_brand_posts', 0)
        display_brand_collaborations(brand_collabs, total_brand_posts)
    
    with tab5:
        if audience_analysis:
            display_audience_analysis(audience_analysis)
        else:
            st.info("No audience analysis data available")
    
    with tab6:
        st.markdown("### 📝 Complete Analytics Summary")
        
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.write("**Profile Overview**")
            st.write(f"""
            - Username: @{profile_info.get('username', 'N/A')}
            - Display Name: {profile_info.get('display_name', 'N/A')}
            - Followers: {format_large_number(engagement_metrics.get('followers', 0))}
            - Following: {format_large_number(engagement_metrics.get('following', 0))}
            - Total Posts: {format_large_number(engagement_metrics.get('total_posts', 0))}
            - Verified: {'✅ Yes' if profile_info.get('is_verified') else '❌ No'}
            - Business Account: {'✅ Yes' if profile_info.get('is_business') else '❌ No'}
            - Category: {profile_info.get('category', 'N/A')}
            - Location: {profile_info.get('location', 'N/A')}
            """)
        
        with summary_col2:
            st.write("**Engagement Overview**")
            st.write(f"""
            - Engagement Rate: {engagement_metrics.get('engagement_rate', 0):.2f}%
            - Avg Likes per Post: {format_large_number(engagement_metrics.get('average_likes', 0))}
            - Avg Comments per Post: {format_large_number(engagement_metrics.get('average_comments', 0))}
            - Avg Views per Post: {format_large_number(engagement_metrics.get('average_views', 0))}
            - Posts Per Week: {round(engagement_metrics.get('posts_per_week', 0), 2)}
            """)
        
        st.markdown("---")
        
        summary_col3, summary_col4 = st.columns(2)
        
        with summary_col3:
            st.write("**Content Overview**")
            content_types = content_analysis.get('content_type_distribution', {})
            st.write(f"""
            - Total Brand Posts: {content_analysis.get('total_brand_posts', 0)}
            - Content Types: {', '.join([f'{k}: {v}' for k, v in content_types.items()])}
            - Top Hashtags: {len(content_analysis.get('top_hashtags', []))}
            - Top Mentions: {len(content_analysis.get('top_mentions', []))}
            """)
        
        with summary_col4:
            st.write("**Trend Overview**")
            if trend_analysis:
                st.write(f"""
                - Viral Posts: {trend_analysis.get('viral_posts_count', 0)}
                - Viral Percentage: {trend_analysis.get('viral_video_percentage', 0):.2f}%
                - Total Posts Analyzed: {data.get('posts_analyzed', 0)}
                - Failed Posts: {data.get('posts_failed', 0)}
                """)
            else:
                st.write("No trend data available")
        
        # Add data export option
        st.markdown("---")
        st.markdown("### 💾 Export Data")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            # JSON download
            json_str = json.dumps(data, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"{profile_info.get('username', 'profile')}_analytics.json",
                mime="application/json"
            )
        
        with col_exp2:
            # CSV download for engagement metrics
            if trend_analysis and trend_analysis.get('engagement_timeline'):
                timeline_df = pd.DataFrame(trend_analysis['engagement_timeline'])
                csv = timeline_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Timeline CSV",
                    data=csv,
                    file_name=f"{profile_info.get('username', 'profile')}_timeline.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
