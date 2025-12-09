import instaloader
import json
from datetime import datetime, timedelta
from collections import Counter
import time
import requests
import os

class InstagramAnalyticsScraper:
    def __init__(self, gemini_api_key=None):
        """
        Initialize the Instagram scraper with Instaloader
        
        Args:
            gemini_api_key: Optional API key for Gemini API integration
        """
        # Configure Instaloader with rate limit handling
        self.loader = instaloader.Instaloader(
            download_pictures=False,  # Don't download images (saves bandwidth)
            download_videos=False,    # Don't download videos
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            max_connection_attempts=3  # Retry failed connections
        )
        self.gemini_api_key = gemini_api_key
        self.request_count = 0  # Track requests for rate limiting
        
    def login(self, username, password):
        """
        Login to Instagram (optional but helps avoid rate limits)
        
        Args:
            username: Instagram username
            password: Instagram password
        """
        try:
            # Try to load existing session
            session_file = f".instaloader-session-{username}"
            if os.path.exists(session_file):
                print(f"📂 Loading existing session for {username}...")
                self.loader.load_session_from_file(username)
                print(f"✓ Successfully loaded session for {username}")
                return True
            
            # If no session exists, login
            print(f"🔐 Logging in as {username}...")
            self.loader.login(username, password)
            
            # Save session for future use
            self.loader.save_session_to_file(session_file)
            print(f"✓ Successfully logged in as {username}")
            print(f"💾 Session saved to {session_file}")
            return True
            
        except instaloader.exceptions.BadCredentialsException:
            print(f"✗ Login failed: Invalid username or password")
            return False
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            print(f"✗ Login failed: Two-factor authentication is enabled")
            print(f"💡 Please disable 2FA temporarily or use an app-specific password")
            return False
        except Exception as e:
            print(f"✗ Login failed: {str(e)}")
            return False
    
    def get_profile_info(self, profile):
        """Extract basic profile information"""
        return {
            'username': profile.username,
            'display_name': profile.full_name,
            'bio': profile.biography,
            'is_verified': profile.is_verified,
            'is_business': profile.is_business_account,
            'profile_pic_url': profile.profile_pic_url,
            'external_url': profile.external_url,
        }
    
    def get_engagement_metrics(self, profile, posts_data):
        """Calculate engagement metrics"""
        total_likes = sum(p['likes'] for p in posts_data)
        total_comments = sum(p['comments'] for p in posts_data)
        total_views = sum(p['views'] for p in posts_data if p['views'] > 0)
        posts_with_views = sum(1 for p in posts_data if p['views'] > 0)
        
        avg_likes = total_likes / len(posts_data) if posts_data else 0
        avg_comments = total_comments / len(posts_data) if posts_data else 0
        avg_views = total_views / posts_with_views if posts_with_views > 0 else 0
        
        # Engagement rate: (Likes + Comments) / Followers × 100
        engagement_rate = ((total_likes + total_comments) / (len(posts_data) * profile.followers)) * 100 if posts_data and profile.followers > 0 else 0
        
        return {
            'followers': profile.followers,
            'following': profile.followees,
            'total_posts': profile.mediacount,
            'average_likes': round(avg_likes, 2),
            'average_comments': round(avg_comments, 2),
            'average_views': round(avg_views, 2),
            'engagement_rate': round(engagement_rate, 2)
        }
    
    def calculate_posts_per_week(self, posts_data):
        """Calculate posting frequency"""
        if not posts_data:
            return 0
        
        dates = [p['date'] for p in posts_data]
        if len(dates) < 2:
            return 0
        
        date_range = (max(dates) - min(dates)).days
        weeks = date_range / 7 if date_range > 0 else 1
        
        return round(len(posts_data) / weeks, 2)
    
    def analyze_content(self, posts_data):
        """Analyze content types and patterns"""
        content_types = Counter()
        all_hashtags = []
        mentioned_users = []
        brand_keywords = ['ad', 'sponsored', 'partnership', 'collab', 'gifted', '#ad', '#sponsored']
        brand_collabs = []
        
        for post in posts_data:
            # Content type
            content_types[post['type']] += 1
            
            # Hashtags
            all_hashtags.extend(post['hashtags'])
            
            # Mentioned users
            mentioned_users.extend(post['mentions'])
            
            # Brand collaborations
            caption_lower = post['caption'].lower()
            if any(keyword in caption_lower for keyword in brand_keywords):
                brand_collabs.append({
                    'post_url': post['url'],
                    'date': post['date'].strftime('%Y-%m-%d'),
                    'caption_snippet': post['caption'][:100]
                })
        
        # Get most common
        top_hashtags = Counter(all_hashtags).most_common(10)
        top_mentions = Counter(mentioned_users).most_common(10)
        
        return {
            'content_type_distribution': dict(content_types),
            'top_hashtags': [{'tag': tag, 'count': count} for tag, count in top_hashtags],
            'top_mentions': [{'user': user, 'count': count} for user, count in top_mentions],
            'brand_collaborations': brand_collabs,
            'total_brand_posts': len(brand_collabs)
        }
    
    def analyze_trends(self, posts_data):
        """Analyze engagement trends and viral content"""
        if not posts_data:
            return {
                'viral_video_percentage': 0,
                'viral_posts_count': 0,
                'engagement_timeline': [],
                'top_performing_posts': []
            }
        
        # Calculate average engagement for baseline
        avg_engagement = sum(p['likes'] + p['comments'] for p in posts_data) / len(posts_data)
        
        # Identify viral posts (3x average engagement)
        viral_threshold = avg_engagement * 3
        viral_posts = [p for p in posts_data if (p['likes'] + p['comments']) >= viral_threshold]
        viral_percentage = (len(viral_posts) / len(posts_data)) * 100
        
        # Engagement over time (last 10 posts)
        recent_posts = sorted(posts_data, key=lambda x: x['date'], reverse=True)[:10]
        engagement_timeline = [
            {
                'date': p['date'].strftime('%Y-%m-%d'),
                'engagement_rate': round(((p['likes'] + p['comments']) / p.get('followers_at_time', 1)) * 100, 2) if 'followers_at_time' in p else 0,
                'likes': p['likes'],
                'comments': p['comments']
            }
            for p in recent_posts
        ]
        
        return {
            'viral_video_percentage': round(viral_percentage, 2),
            'viral_posts_count': len(viral_posts),
            'engagement_timeline': engagement_timeline,
            'top_performing_posts': sorted(
                posts_data,
                key=lambda x: x['likes'] + x['comments'],
                reverse=True
            )[:5]
        }
    
    def get_category_from_gemini(self, profile_data):
        """Use Gemini API to infer account category"""
        if not self.gemini_api_key:
            return "Unknown (Gemini API key not provided)"
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}"
            
            prompt = f"""Based on this Instagram profile information, determine the account category/niche (e.g., Fashion, Food, Travel, Tech, Fitness, etc.). 
            Be specific and concise, return only the category name.
            
            Username: {profile_data.get('username')}
            Display Name: {profile_data.get('display_name')}
            Bio: {profile_data.get('bio')}
            
            Category:"""
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                category = result['candidates'][0]['content']['parts'][0]['text'].strip()
                return category
            else:
                return "Unknown (API error)"
        except Exception as e:
            return f"Unknown (Error: {str(e)})"
    
    def get_location_from_gemini(self, profile_data):
        """Use Gemini API to infer location"""
        if not self.gemini_api_key:
            return "Unknown (Gemini API key not provided)"
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}"
            
            prompt = f"""Based on this Instagram profile information, infer the person's location (city/country). 
            Be specific if possible, otherwise provide best guess. Return only the location.
            
            Username: {profile_data.get('username')}
            Display Name: {profile_data.get('display_name')}
            Bio: {profile_data.get('bio')}
            External URL: {profile_data.get('external_url')}
            
            Location:"""
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                location = result['candidates'][0]['content']['parts'][0]['text'].strip()
                return location
            else:
                return "Unknown (API error)"
        except Exception as e:
            return f"Unknown (Error: {str(e)})"
    
    def scrape_profile(self, username, max_posts=50, delay_between_posts=2):
        """
        Main scraping function - extracts all analytics data
        
        Args:
            username: Instagram username to scrape
            max_posts: Maximum number of recent posts to analyze (can be 100+)
            delay_between_posts: Seconds to wait between post fetches (2-4 recommended)
        
        Returns:
            dict: Complete analytics data
        """
        try:
            print(f"\n🔍 Scraping profile: @{username}")
            print("=" * 60)
            print(f"⚙️  Settings: max_posts={max_posts}, delay={delay_between_posts}s")
            
            # Check if logged in
            if not self.loader.context.username:
                print("\n⚠️  WARNING: Not logged in! This may fail with 401 errors.")
                print("💡 Please use scraper.login('username', 'password') before scraping.")
                response = input("Continue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    print("❌ Scraping cancelled. Please login first.")
                    return None
            
            # Load profile
            try:
                profile = instaloader.Profile.from_username(self.loader.context, username)
            except Exception as e:
                if "401" in str(e) or "Unauthorized" in str(e):
                    print(f"\n❌ 401 Unauthorized Error!")
                    print(f"💡 This error means Instagram is blocking unauthenticated requests.")
                    print(f"\n🔧 SOLUTIONS:")
                    print(f"   1. Login using: scraper.login('your_username', 'your_password')")
                    print(f"   2. Make sure you're using valid Instagram credentials")
                    print(f"   3. If you have 2FA, disable it temporarily or use backup codes")
                    print(f"   4. Wait 30 minutes if you've been rate limited")
                    return None
                raise
            
            print(f"✓ Profile loaded")
            self.request_count += 1
            
            # Get basic profile info
            profile_info = self.get_profile_info(profile)
            print(f"✓ Profile information extracted")
            
            # Get posts data
            print(f"📥 Fetching last {max_posts} posts...")
            print(f"⏱️  Estimated time: ~{(max_posts * delay_between_posts) / 60:.1f} minutes")
            posts_data = []
            post_count = 0
            failed_posts = 0
            
            for post in profile.get_posts():
                if post_count >= max_posts:
                    break
                
                try:
                    posts_data.append({
                        'url': f"https://www.instagram.com/p/{post.shortcode}/",
                        'date': post.date_local,
                        'likes': post.likes,
                        'comments': post.comments,
                        'views': post.video_view_count if post.is_video else 0,
                        'type': 'Video' if post.is_video else 'Photo',
                        'caption': post.caption if post.caption else '',
                        'hashtags': post.caption_hashtags,
                        'mentions': post.caption_mentions,
                        'followers_at_time': profile.followers  # Approximate
                    })
                    post_count += 1
                    self.request_count += 1
                    
                    # Progress updates
                    if post_count % 10 == 0:
                        print(f"  → Processed {post_count}/{max_posts} posts (Failed: {failed_posts})")
                    
                    # Adaptive rate limiting
                    if post_count % 20 == 0:
                        # Longer pause every 20 posts
                        print(f"  ⏸️  Taking a longer break to avoid rate limits...")
                        time.sleep(delay_between_posts * 3)
                    else:
                        time.sleep(delay_between_posts)
                        
                except instaloader.exceptions.QueryReturnedNotFoundException:
                    failed_posts += 1
                    print(f"  ⚠ Post {post.shortcode} not found (deleted/unavailable)")
                    continue
                except instaloader.exceptions.ConnectionException as e:
                    failed_posts += 1
                    print(f"  ⚠ Connection error for post {post.shortcode}: {str(e)}")
                    print(f"  ⏸️  Waiting 30 seconds before continuing...")
                    time.sleep(30)
                    continue
                except Exception as e:
                    failed_posts += 1
                    print(f"  ⚠ Warning: Could not process post {post.shortcode}: {str(e)}")
                    continue
            
            print(f"✓ Fetched {len(posts_data)} posts (Failed: {failed_posts})")
            print(f"📊 Total API requests made: {self.request_count}")
            
            # Calculate metrics
            print("📊 Calculating analytics...")
            engagement_metrics = self.get_engagement_metrics(profile, posts_data)
            posts_per_week = self.calculate_posts_per_week(posts_data)
            content_analysis = self.analyze_content(posts_data)
            trend_analysis = self.analyze_trends(posts_data)
            
            # Get AI-powered insights
            print("🤖 Getting AI-powered insights...")
            category = self.get_category_from_gemini(profile_info)
            location = self.get_location_from_gemini(profile_info)
            
            # Compile results
            analytics = {
                'profile_information': {
                    **profile_info,
                    'category': category,
                    'location': location
                },
                'engagement_metrics': {
                    **engagement_metrics,
                    'posts_per_week': posts_per_week
                },
                'content_analysis': content_analysis,
                'trend_analysis': trend_analysis,
                'scraped_at': datetime.now().isoformat(),
                'posts_analyzed': len(posts_data),
                'posts_failed': failed_posts,
                'total_requests': self.request_count
            }
            
            print("\n✅ Scraping completed successfully!")
            return analytics
            
        except instaloader.exceptions.ProfileNotExistsException:
            print(f"✗ Error: Profile @{username} does not exist")
            return None
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            print(f"✗ Error: Profile @{username} is private. Please login and follow this account.")
            return None
        except instaloader.exceptions.TooManyRequestsException:
            print(f"✗ Error: Rate limit exceeded! Instagram has temporarily blocked requests.")
            print(f"💡 Suggestions:")
            print(f"   - Wait 30-60 minutes before trying again")
            print(f"   - Login to your Instagram account using scraper.login()")
            print(f"   - Reduce max_posts parameter")
            print(f"   - Increase delay_between_posts (current: 2s, try: 4-5s)")
            return None
        except instaloader.exceptions.ConnectionException as e:
            print(f"✗ Connection Error: {str(e)}")
            print(f"💡 This might be a rate limit. Try again in 30 minutes.")
            return None
        except Exception as e:
            print(f"✗ Error scraping profile: {str(e)}")
            return None
    
    def save_results(self, analytics, filename=None):
        """Save analytics results to JSON file"""
        if not analytics:
            print("No data to save")
            return
        
        if not filename:
            username = analytics['profile_information']['username']
            filename = f"{username}_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Deep copy and convert
        def serialize(data):
            if isinstance(data, dict):
                return {k: serialize(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [serialize(item) for item in data]
            elif isinstance(data, datetime):
                return data.isoformat()
            else:
                return data
        
        serialized_data = serialize(analytics)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename


# Example usage
if __name__ == "__main__":
    # Initialize scraper
    GEMINI_API_KEY = "AIzaSyA4Om8gNEzW8tqPBMmCZCxpTfbc3Dd2-mI"
    scraper = InstagramAnalyticsScraper(gemini_api_key=GEMINI_API_KEY)
    
    # SOLUTION TO 401 ERROR: Must login to Instagram!
    print("\n⚠️  Instagram requires authentication!")
    print("Please enter your Instagram credentials:")
    
    insta_username = input("Instagram Username: ").strip()
    insta_password = input("Instagram Password: ").strip()
    
    if not scraper.login(insta_username, insta_password):
        print("\n❌ Login failed! Please check your credentials and try again.")
        print("💡 Tips:")
        print("   - Make sure your username and password are correct")
        print("   - If you have 2FA enabled, you may need to approve the login")
        print("   - Try using a dedicated account for scraping")
        exit(1)
    
    # Scrape profile
    username = input("\nEnter Instagram username to scrape (e.g., virat.kohli): ").strip()
    max_posts = int(input("Number of posts to analyze (recommended: 30-100, press Enter for 100): ").strip() or "100")
    
    # RATE LIMIT GUIDELINES:
    # - With login: max_posts=100-200 (recommended: 100)
    # - delay_between_posts: 2-4 seconds (higher = safer)
    
    print(f"\n🚀 Starting scrape with {max_posts} posts...")
    print(f"⏱️  Estimated time: ~{(max_posts * 3) / 60:.1f} minutes")
    
    analytics = scraper.scrape_profile(
        username, 
        max_posts=max_posts,
        delay_between_posts=3  # 3 seconds between posts (safer)
    )
    
    # Display summary
    if analytics:
        print("\n" + "=" * 60)
        print("📊 ANALYTICS SUMMARY")
        print("=" * 60)
        
        profile = analytics.get('profile_information', {})
        metrics = analytics.get('engagement_metrics', {})
        content = analytics.get('content_analysis', {})
        trends = analytics.get('trend_analysis', {})
        
        print(f"\n👤 PROFILE: @{profile.get('username', 'N/A')}")
        print(f"   Name: {profile.get('display_name', 'N/A')}")
        print(f"   Category: {profile.get('category', 'N/A')}")
        print(f"   Location: {profile.get('location', 'N/A')}")
        bio_text = profile.get('bio', 'N/A')
        print(f"   Bio: {bio_text[:100]}..." if len(bio_text) > 100 else f"   Bio: {bio_text}")
        
        print(f"\n📈 ENGAGEMENT:")
        print(f"   Followers: {metrics.get('followers', 0):,}")
        print(f"   Following: {metrics.get('following', 0):,}")
        print(f"   Total Posts: {metrics.get('total_posts', 0):,}")
        print(f"   Engagement Rate: {metrics.get('engagement_rate', 0)}%")
        print(f"   Avg Likes: {metrics.get('average_likes', 0):,}")
        print(f"   Avg Comments: {metrics.get('average_comments', 0):,}")
        print(f"   Avg Views: {metrics.get('average_views', 0):,}")
        print(f"   Posts/Week: {metrics.get('posts_per_week', 0)}")
        
        print(f"\n📝 CONTENT:")
        print(f"   Content Types: {content.get('content_type_distribution', {})}")
        print(f"   Brand Collaborations: {content.get('total_brand_posts', 0)}")
        top_hashtags = content.get('top_hashtags', [])
        if top_hashtags:
            print(f"   Top Hashtags: {[h['tag'] for h in top_hashtags[:5]]}")
        else:
            print(f"   Top Hashtags: None found")
        
        print(f"\n🔥 TRENDS:")
        print(f"   Viral Posts: {trends.get('viral_posts_count', 0)} ({trends.get('viral_video_percentage', 0)}%)")
        
        # Save to file
        scraper.save_results(analytics)
    else:
        print("\n❌ Failed to scrape profile. Please check the errors above.")
    
    print("\n" + "=" * 60)