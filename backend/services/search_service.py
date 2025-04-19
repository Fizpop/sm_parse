import os
import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import feedparser
from urllib.parse import urlparse, quote, unquote
import json
import concurrent.futures
import time
import urllib3
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from newspaper import Article
from duckduckgo_search import DDGS

# Вимикаємо попередження про незахищені HTTPS запити
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            logging.info("WebDriver initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {str(e)}")
            self.driver = None

    def __del__(self):
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver closed successfully")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {str(e)}")

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            # Видаляємо www. якщо воно є
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return ""

    def clean_text(self, text: str) -> str:
        """Clean text from HTML and extra spaces."""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def is_news_website(self, url, content=None):
        score = 0
        
        # URL-based checks
        news_indicators = ['news', 'article', 'story', 'press', 'media', 'journal']
        url_lower = url.lower()
        for indicator in news_indicators:
            if indicator in url_lower:
                score += 1

        # Content-based checks if available
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for article tags
            if soup.find('article'):
                score += 2
            
            # Check for publication date
            date_patterns = ['date', 'published', 'time', 'posted']
            for pattern in date_patterns:
                if soup.find(attrs={'class': lambda x: x and pattern in x.lower() if x else False}):
                    score += 1
            
            # Check for social media sharing buttons
            social_patterns = ['share', 'twitter', 'facebook', 'linkedin']
            for pattern in social_patterns:
                if soup.find(attrs={'class': lambda x: x and pattern in x.lower() if x else False}):
                    score += 1

        return score >= 3

    def get_real_url(self, url):
        if not url:
            return None

        if not self.driver:
            self.setup_driver()
            if not self.driver:
                return url

        try:
            self.driver.get(url)
            time.sleep(2)  # Wait for any JavaScript redirects

            current_url = self.driver.current_url
            
            # If still on Google News, try to find the actual link
            if 'news.google.com' in current_url:
                links = self.driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and 'news.google.com' not in href and 'accounts.google.com' not in href:
                        return href
            
            return current_url
        except Exception as e:
            logging.error(f"Error getting real URL for {url}: {str(e)}")
            return url

    def get_rss_feed(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
            return feed
        except Exception as e:
            logging.error(f"Error fetching RSS feed from {url}: {str(e)}")
            return None

    def analyze_website(self, url):
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            metadata = {
                'title': article.title,
                'description': article.meta_description,
                'is_news': self.is_news_website(url, article.html)
            }
            
            return metadata
        except Exception as e:
            logging.error(f"Error analyzing website {url}: {str(e)}")
            return None

    def search_google_news(self, query, max_results=10):
        base_url = "https://news.google.com/rss/search?q="
        encoded_query = quote(query)
        rss_url = f"{base_url}{encoded_query}"
        
        feed = self.get_rss_feed(rss_url)
        if not feed:
            return []
        
        results = []
        for entry in feed.entries[:max_results]:
            real_url = self.get_real_url(entry.link)
            if real_url:
                results.append({
                    'title': entry.title,
                    'url': real_url,
                    'source': 'Google News'
                })
        
        return results

    def search_media(self, query, max_results=20):
        results = []
        seen_urls = set()

        # Search using DuckDuckGo
        try:
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
                for result in ddg_results:
                    url = result['link']
                    if url not in seen_urls:
                        metadata = self.analyze_website(url)
                        if metadata and metadata['is_news']:
                            results.append({
                                'title': result['title'],
                                'url': url,
                                'description': result['body'],
                                'source': 'DuckDuckGo'
                            })
                            seen_urls.add(url)
        except Exception as e:
            logging.error(f"Error searching DuckDuckGo: {str(e)}")

        # Search using Google News
        try:
            google_results = self.search_google_news(query, max_results=max_results)
            for result in google_results:
                url = result['url']
                if url not in seen_urls:
                    results.append(result)
                    seen_urls.add(url)
        except Exception as e:
            logging.error(f"Error searching Google News: {str(e)}")

        return results[:max_results]

search_service = SearchService() 