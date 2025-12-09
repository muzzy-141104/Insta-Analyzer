# 📊 Instagram Analytics Dashboard

Beautiful Streamlit dashboard for analyzing Instagram profiles with comprehensive metrics, trends, and visualizations.

## ✨ Features

- 🔍 **Scrape Instagram Profiles** - Get detailed analytics for any public profile
- 📊 **Engagement Metrics** - Likes, comments, views, engagement rates
- 📈 **Trend Analysis** - Viral posts, engagement timeline, top performers
- 💼 **Brand Collaborations** - Detect sponsored content
- 📉 **Interactive Charts** - Plotly visualizations with export options
- 💾 **Data Export** - Download as JSON or CSV

## 🚀 Quick Start

### Local Setup

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the app**
```bash
streamlit run app.py
```

3. **Open browser** to `http://localhost:8501`

### Using the Dashboard

1. **View Analytics** - Browse existing analytics from dropdown
2. **Scrape New Profile** - Enter Instagram username, login (optional), and scrape

## ☁️ Deploy to Cloud (FREE)

### Streamlit Cloud (Recommended)

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Instagram Analytics Dashboard"
git remote add origin https://github.com/YOUR_USERNAME/insta-analyzer.git
git push -u origin main
```

2. **Deploy**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app" → Select your repo
   - Set main file: `app.py`
   - Click "Deploy!"

3. **Done!** Your app will be live at: `https://your-username-insta-analyzer.streamlit.app`

### Heroku

```bash
heroku create your-app-name
git push heroku main
```

## 📁 Project Structure

```
insta_analyzer/
├── app.py              # Main Streamlit dashboard
├── main.py             # CLI scraper (optional)
├── analytics.py        # Analytics engine
├── config.py           # Configuration
├── requirements.txt    # Dependencies
└── Procfile           # For Heroku deployment
copy .env.example .env

# Edit .env and add your Gemini API key (optional)
# This enables AI-powered category and location inference
```

### Running the Application

#### Option 1: Run Streamlit Dashboard (Recommended)
```bash
streamlit run app.py
```
Then open your browser to `http://localhost:8501`

#### Option 2: Run CLI Scraper
```bash
python main.py
```

## 📖 Usage Guide

### Using the Dashboard

1. **Start the application**
   ```bash
   streamlit run app.py
```

## � Usage

### Scraping Profiles
- Login with your Instagram account (optional but recommended)
- Enter target username
- Configure posts count (10-100) and delay (2-5 sec)
- Wait for scraping to complete

### Viewing Analytics
- Select profile from dropdown
- Explore 6 tabs: Content, Engagement, Trends, Brand Collabs, Audience, Summary
- Export data as JSON/CSV

## ⚠️ Important Notes

- **Login recommended** to avoid rate limits and 401 errors
- **Use delays** of 2-4 seconds between requests
- **Scraping is intentionally slow** to respect Instagram's limits
- Only works with **public profiles**

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Login with your Instagram account |
| Rate limit exceeded | Wait 30-60 min, increase delay |
| Scraping is slow | Normal behavior to avoid rate limits |

## � License

This project is for educational and research purposes.

---

**Made with ❤️ for Instagram Analytics**


This project is for educational and research purposes.

## 🙏 Acknowledgments

- **Instaloader**: Instagram scraping library
- **Streamlit**: Dashboard framework
- **Plotly**: Visualization library

## 📞 Support

For issues or questions:
1. Check this README
2. Review existing analytics files for examples
3. Test with small post counts first (10-20)
4. Ensure you're logged in to Instagram

---

**Made with ❤️ for Instagram Analytics**

*Last Updated: December 2025*
