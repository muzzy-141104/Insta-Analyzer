import statistics
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import logging
from dateutil import parser as dateparser

logger = logging.getLogger("analytics")


def _ensure_dt(v) -> Optional[datetime]:
    """Coerce many date forms to datetime or return None."""
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    try:
        return dateparser.parse(str(v))
    except Exception:
        return None


class InstagramAnalytics:
    """Advanced analytics engine for Instagram data"""

    def __init__(self):
        self.brand_keywords = [
            "#ad", "#sponsored", "#partner", "#collab", "sponsored", "paid partnership",
            "#gifted", "#gift", "thanks", "ambassador", "#ambassador", "collaboration",
            "in collaboration with", "partnership with", "sponsored by"
        ]
        self.viral_threshold_multiplier = 3.0  # 3x median engagement = viral

    def _empty_engagement_metrics(self) -> Dict[str, Any]:
        return {
            "avg_likes": 0,
            "avg_comments": 0,
            "avg_engagement_per_post": 0,
            "engagement_rate_percent": 0,
            "median_engagement": 0,
            "max_engagement": 0,
            "min_engagement": 0,
            "viral_posts_count": 0,
            "viral_percentage": 0,
            "viral_threshold": 0,
            "top_performing_posts": []
        }

    def calculate_engagement_metrics(self, posts_data: List[Dict], followers: int) -> Dict[str, Any]:
        """Calculate comprehensive engagement metrics"""
        if not posts_data:
            return self._empty_engagement_metrics()

        # Normalize date fields first
        for p in posts_data:
            if p.get("date"):
                p["date"] = _ensure_dt(p["date"])

        total_likes = sum(p.get("likes", 0) for p in posts_data)
        total_comments = sum(p.get("comments", 0) for p in posts_data)
        total_engagement = total_likes + total_comments
        post_count = len(posts_data)

        avg_likes = total_likes / post_count if post_count else 0
        avg_comments = total_comments / post_count if post_count else 0
        avg_engagement_per_post = total_engagement / post_count if post_count else 0
        er_percent = (avg_engagement_per_post / followers) * 100 if followers > 0 else 0

        engagement_values = [p.get("engagement", 0) for p in posts_data]
        median_engagement = statistics.median(engagement_values) if engagement_values else 0
        max_engagement = max(engagement_values) if engagement_values else 0
        min_engagement = min(engagement_values) if engagement_values else 0

        viral_threshold = median_engagement * self.viral_threshold_multiplier
        viral_posts = [p for p in posts_data if p.get("engagement", 0) > viral_threshold]
        viral_percentage = (len(viral_posts) / post_count) * 100 if post_count > 0 else 0

        top_posts = sorted(posts_data, key=lambda x: x.get("engagement", 0), reverse=True)[:5]

        return {
            "avg_likes": round(avg_likes, 2),
            "avg_comments": round(avg_comments, 2),
            "avg_engagement_per_post": round(avg_engagement_per_post, 2),
            "engagement_rate_percent": round(er_percent, 3),
            "median_engagement": round(median_engagement, 2),
            "max_engagement": max_engagement,
            "min_engagement": min_engagement,
            "viral_posts_count": len(viral_posts),
            "viral_percentage": round(viral_percentage, 2),
            "viral_threshold": round(viral_threshold, 2),
            "top_performing_posts": [
                {
                    "shortcode": p.get("shortcode"),
                    "engagement": p.get("engagement"),
                    "date": p.get("date").isoformat() if isinstance(p.get("date"), datetime) else p.get("date"),
                    "type": p.get("type"),
                } for p in top_posts
            ],
        }

    def analyze_content_types(self, posts_data: List[Dict]) -> Dict[str, Any]:
        """Analyze content type distribution and performance"""
        if not posts_data:
            return {"types": {}, "counts": {}, "top_performing": {}}

        counts = {"Photo": 0, "Reel/Video": 0, "Carousel": 0, "Unknown": 0}
        engagement_by_type = {"Photo": [], "Reel/Video": [], "Carousel": [], "Unknown": []}

        for p in posts_data:
            t = p.get("type", "Unknown")
            counts[t] = counts.get(t, 0) + 1
            engagement_by_type.setdefault(t, []).append(p.get("engagement", 0))

        avg_by_type = {k: (statistics.mean(v) if v else 0) for k, v in engagement_by_type.items()}
        most_effective_type = max(avg_by_type.items(), key=lambda x: x[1])[0] if avg_by_type else None

        return {
            "types": counts,
            "avg_engagement_by_type": {k: round(v, 2) for k, v in avg_by_type.items()},
            "most_effective_type": most_effective_type,
        }

    def detect_brand_collaborations(self, posts_data: List[Dict]) -> Dict[str, Any]:
        """Detect sponsored posts using caption heuristics. Return rates and examples."""
        if not posts_data:
            return {"collaboration_count": 0, "collaboration_rate_percent": 0.0, "examples": []}

        collab_posts = []
        for p in posts_data:
            caption = (p.get("caption") or "").lower()
            tags = p.get("hashtags", []) or []
            # keyword check in caption or hashtags
            if any(kw in caption for kw in self.brand_keywords) or any(kw in (tag.lower() for tag in tags) for kw in self.brand_keywords):
                collab_posts.append(p)

        rate = (len(collab_posts) / len(posts_data)) * 100 if posts_data else 0
        samples = [{"shortcode": p.get("shortcode"), "caption": (p.get("caption") or "")[:200]} for p in collab_posts[:10]]

        return {"collaboration_count": len(collab_posts), "collaboration_rate_percent": round(rate, 2), "examples": samples}

    def analyze_hashtags_and_mentions(self, posts_data: List[Dict]) -> Dict[str, Any]:
        """Aggregate hashtags and mentions frequency."""
        if not posts_data:
            return {"top_hashtags": [], "top_mentions": [], "total_unique_hashtags": 0}

        hashtags = {}
        mentions = {}
        for p in posts_data:
            for h in (p.get("hashtags") or []):
                tag = h.lower().lstrip("#")
                hashtags[tag] = hashtags.get(tag, 0) + 1
            for m in (p.get("mentions") or []):
                mentions[m.lower()] = mentions.get(m.lower(), 0) + 1

        top_hashtags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)[:20]
        top_mentions = sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:20]

        return {"top_hashtags": top_hashtags, "top_mentions": top_mentions, "total_unique_hashtags": len(hashtags)}

    def calculate_posting_frequency(self, posts_data: List[Dict]) -> Dict[str, Any]:
        """Calculate posting frequency metrics using robust date parsing."""
        if not posts_data:
            return {
                "total_analyzed_posts": 0,
                "analysis_period_days": 0,
                "posts_per_day": 0,
                "posts_per_week": 0,
                "posts_per_month": 0,
                "recent_posts_per_week": 0,
                "avg_days_between_posts": 0,
                "median_days_between_posts": 0,
                "posting_consistency": "Unknown",
                "most_active_day": None,
            }

        # Normalize dates
        dates = [_ensure_dt(p.get("date")) for p in posts_data if p.get("date")]
        dates = sorted([d for d in dates if d is not None], reverse=True)
        if not dates:
            return {
                "total_analyzed_posts": len(posts_data),
                "analysis_period_days": 0,
                "posts_per_day": 0,
                "posts_per_week": 0,
                "posts_per_month": 0,
                "recent_posts_per_week": 0,
                "avg_days_between_posts": 0,
                "median_days_between_posts": 0,
                "posting_consistency": "Unknown",
                "most_active_day": None,
            }

        total_posts = len(dates)
        newest = dates[0]
        oldest = dates[-1]
        total_days = max(1, (newest - oldest).days or 1)

        posts_per_day = total_posts / total_days if total_days > 0 else total_posts
        posts_per_week = posts_per_day * 7
        posts_per_month = posts_per_day * 30

        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_posts = [d for d in dates if d > thirty_days_ago]
        recent_posts_per_week = (len(recent_posts) / 30) * 7 if len(recent_posts) > 0 else 0

        # Activity by weekday
        day_activity = {}
        for d in dates:
            day_name = d.strftime("%A")
            day_activity[day_name] = day_activity.get(day_name, 0) + 1

        # Gaps between posts (in days)
        gaps = []
        for i in range(len(dates) - 1):
            diff = (dates[i] - dates[i + 1]).days
            gaps.append(diff)
        avg_gap = statistics.mean(gaps) if gaps else 0
        median_gap = statistics.median(gaps) if gaps else 0

        consistency = "High" if avg_gap < 2 else "Medium" if avg_gap < 5 else "Low"
        most_active_day = max(day_activity.items(), key=lambda x: x[1])[0] if day_activity else None

        return {
            "total_analyzed_posts": total_posts,
            "analysis_period_days": total_days,
            "posts_per_day": round(posts_per_day, 2),
            "posts_per_week": round(posts_per_week, 2),
            "posts_per_month": round(posts_per_month, 2),
            "recent_posts_per_week": round(recent_posts_per_week, 2),
            "avg_days_between_posts": round(avg_gap, 1),
            "median_days_between_posts": round(median_gap, 1),
            "posting_consistency": consistency,
            "most_active_day": most_active_day,
            "day_activity": day_activity,
        }

    def analyze_engagement_trends(self, posts_data: List[Dict], followers: int) -> Dict[str, Any]:
        """Analyze engagement rate over time and produce a simple trend assessment."""
        if not posts_data:
            return {"trend": "Insufficient data", "timeline": []}

        # Ensure dates normalized
        posts = []
        for p in posts_data:
            d = _ensure_dt(p.get("date"))
            if d:
                posts.append({**p, "date": d})

        sorted_posts = sorted(posts, key=lambda x: x["date"], reverse=True)
        timeline = []
        for p in sorted_posts:
            engagement_rate = (p.get("engagement", 0) / followers) * 100 if followers > 0 else 0
            timeline.append({
                "date": p["date"].strftime("%Y-%m-%d"),
                "engagement_rate": round(engagement_rate, 3),
                "likes": p.get("likes", 0),
                "comments": p.get("comments", 0),
                "type": p.get("type", "Unknown"),
                "shortcode": p.get("shortcode"),
            })

        trend = "Insufficient data"
        trend_change_percent = 0
        if len(timeline) >= 10:
            recent_rates = [t["engagement_rate"] for t in timeline[:10]]
            older_rates = [t["engagement_rate"] for t in timeline[-10:]]
            recent_avg = statistics.mean(recent_rates)
            older_avg = statistics.mean(older_rates) or 0.0
            trend_diff = recent_avg - older_avg
            if trend_diff > 0.1:
                trend = "Increasing"
            elif trend_diff < -0.1:
                trend = "Decreasing"
            else:
                trend = "Stable"
            trend_change_percent = (trend_diff / older_avg * 100) if older_avg > 0 else 0

        recent_avg_engagement = statistics.mean([t["engagement_rate"] for t in timeline[:min(10, len(timeline))]]) if timeline else 0
        overall_avg_engagement = statistics.mean([t["engagement_rate"] for t in timeline]) if timeline else 0

        return {
            "trend": trend,
            "trend_change_percent": round(trend_change_percent, 2),
            "timeline": timeline,
            "recent_avg_engagement": round(recent_avg_engagement, 3),
            "overall_avg_engagement": round(overall_avg_engagement, 3),
        }

    def generate_comprehensive_report(self, posts_data: List[Dict], profile_data: Dict) -> Dict[str, Any]:
        """Compose the full analytics report dictionary."""
        followers = profile_data.get("Followers", 0)
        engagement_metrics = self.calculate_engagement_metrics(posts_data, followers)
        content_analysis = self.analyze_content_types(posts_data)
        brand_analysis = self.detect_brand_collaborations(posts_data)
        hashtag_analysis = self.analyze_hashtags_and_mentions(posts_data)
        frequency_analysis = self.calculate_posting_frequency(posts_data)
        trend_analysis = self.analyze_engagement_trends(posts_data, followers)
        score = self._calculate_influence_score(engagement_metrics, brand_analysis, frequency_analysis)

        return {
            "profile_summary": profile_data,
            "engagement_metrics": engagement_metrics,
            "content_analysis": content_analysis,
            "brand_collaborations": brand_analysis,
            "hashtag_analysis": hashtag_analysis,
            "posting_frequency": frequency_analysis,
            "engagement_trends": trend_analysis,
            "influence_score": score,
            "analysis_metadata": {
                "total_posts_analyzed": len(posts_data),
                "analysis_date": datetime.now().isoformat(),
                "data_quality": "Good" if len(posts_data) >= 20 else "Limited" if len(posts_data) >= 5 else "Very Limited"
            }
        }

    def _calculate_influence_score(self, engagement: Dict, brand: Dict, frequency: Dict) -> Dict[str, Any]:
        score_components = {}
        er = engagement.get("engagement_rate_percent", 0)
        viral_pct = engagement.get("viral_percentage", 0)
        engagement_score = min((er * 2) + (viral_pct * 0.5), 40)
        score_components["engagement_score"] = engagement_score

        collab_rate = brand.get("collaboration_rate_percent", 0)
        brand_score = min(collab_rate * 3, 30)
        score_components["brand_score"] = brand_score

        posts_per_week = frequency.get("posts_per_week", 0)
        consistency_score = min(posts_per_week * 2, 20)
        score_components["consistency_score"] = consistency_score

        quality_score = 10
        score_components["quality_score"] = quality_score

        total_score = sum(score_components.values())

        return {"total_score": round(min(total_score, 100), 1), "components": score_components}
