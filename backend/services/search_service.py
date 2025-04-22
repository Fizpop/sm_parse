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
from .domain_service import domain_analyzer

# Вимикаємо попередження про незахищені HTTPS запити
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        self.domain_cache = {}  # Кеш для результатів аналізу доменів

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
        return domain_analyzer.extract_clean_domain(url)

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

    def extract_base_domain(self, url: str) -> str:
        """Витягує базовий домен з URL."""
        try:
            parsed = urlparse(url)
            # Отримуємо основний домен (наприклад, suspilne.media з kyiv.suspilne.media)
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) > 2:
                return '.'.join(domain_parts[-2:])
            return parsed.netloc
        except Exception as e:
            logger.error(f"Error extracting base domain from {url}: {str(e)}")
            return ""

    def get_ai_analysis(self, url: str) -> Optional[Dict]:
        """Отримує аналіз сайту від ШІ сервісу."""
        try:
            # Формуємо промпт з URL прямо в тексті
            prompt = f"""Поверни домен з цього URL публікації: {url}
            
            Формат відповіді:
            {{
                "domain": "домен сайту"
            }}"""
            
            # Відправляємо запит до ШІ (без URL параметра)
            ai_url = f"http://127.0.0.1:8080/?text={quote(prompt)}"
            response = requests.get(ai_url, timeout=30)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result and isinstance(result, dict) and 'domain' in result:
                        return {
                            'domain': result['domain'],
                            'description': ''
                        }
                except Exception as e:
                    logger.error(f"Failed to parse AI response for {url}: {str(e)}")
            
            # Якщо щось пішло не так, витягуємо домен з URL
            return {
                'domain': self.extract_base_domain(url),
                'description': ''
            }
                
        except Exception as e:
            logger.error(f"Error getting AI analysis for {url}: {str(e)}")
            return {
                'domain': self.extract_base_domain(url),
                'description': ''
            }

    def analyze_website(self, url):
        try:
            # Спочатку отримуємо аналіз від ШІ
            ai_analysis = self.get_ai_analysis(url)
            if not ai_analysis:
                return None
                
            try:
                # Пробуємо отримати додаткову інформацію через newspaper3k
                article = Article(url)
                article.download()
                article.parse()
                
                # Доповнюємо аналіз від ШІ даними з article
                if not ai_analysis.get('description'):
                    ai_analysis['description'] = article.meta_description
                    
            except Exception as e:
                logger.warning(f"Failed to get additional info via newspaper3k for {url}: {str(e)}")
                # Продовжуємо роботу навіть якщо newspaper3k не спрацював
                
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing website {url}: {str(e)}")
            return None

    def search_google_news(self, query, max_results=10):
        base_url = "https://news.google.com/rss/search?q="
        encoded_query = quote(query)
        rss_url = f"{base_url}{encoded_query}&hl=uk&gl=UA&ceid=UA:uk"
        
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

    def analyze_media_source(self, url: str) -> Dict:
        """Аналізує медіа-ресурс та його базовий домен."""
        try:
            base_domain = self.extract_base_domain(url)
            
            # Перевіряємо кеш
            if base_domain in self.domain_cache:
                logger.info(f"Using cached analysis for domain {base_domain}")
                return self.domain_cache[base_domain]
            
            # Формуємо промпт для аналізу базового домену
            prompt = """Проаналізуй це медіа-джерело та поверни JSON з такими полями:
            {
                "base_domain": "базовий домен медіа-ресурсу",
                "name": "назва медіа-ресурсу",
                "description": "короткий опис медіа-ресурсу, максимум 200 символів",
                "type": "тип медіа (news, blog, tv, radio, press)",
                "language": "основна мова (uk, en, ru)",
                "coverage": "географія покриття (local, regional, national, international)",
                "reliability_score": число від 0 до 100,
                "social_media": {
                    "facebook": "посилання або null",
                    "twitter": "посилання або null",
                    "telegram": "посилання або null"
                },
                "has_rss": true/false
            }
            """
            
            # Відправляємо запит до ШІ
            ai_url = f"http://127.0.0.1:8080/?text={quote(prompt)}&url={quote(base_domain)}"
            response = requests.get(ai_url, timeout=30)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # Зберігаємо в кеш
                    self.domain_cache[base_domain] = result
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse AI response for {base_domain}")
                    return None
            else:
                logger.error(f"AI service returned status {response.status_code} for {base_domain}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing media source {url}: {str(e)}")
            return None

    def search_media(self, query, max_results=20):
        results = []
        seen_domains = set()

        # Search using DuckDuckGo
        try:
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(
                    query,
                    max_results=max_results,
                    region='ua',
                    safesearch='off',
                    timelimit='m'
                ))
                for result in ddg_results:
                    try:
                        url = result.get('link')
                        if not url:
                            continue
                            
                        # Отримуємо аналіз від ШІ або витягуємо базовий домен
                        media_info = self.get_ai_analysis(url)
                        domain = media_info['domain']
                        
                        if domain and domain not in seen_domains:
                            seen_domains.add(domain)
                            results.append({
                                'url': url,
                                'domain': domain,
                                'description': media_info.get('description', ''),
                                'found_at': str(datetime.utcnow().isoformat())
                            })
                            
                    except Exception as e:
                        logger.error(f"Error processing result: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {str(e)}")

        # Search using Google News
        try:
            google_results = self.search_google_news(query)
            for result in google_results:
                try:
                    url = result.get('url')
                    if not url:
                        continue
                        
                    # Отримуємо аналіз від ШІ або витягуємо базовий домен
                    media_info = self.get_ai_analysis(url)
                    domain = media_info['domain']
                    
                    if domain and domain not in seen_domains:
                        seen_domains.add(domain)
                        results.append({
                            'url': url,
                            'domain': domain,
                            'description': media_info.get('description', ''),
                            'found_at': str(datetime.utcnow().isoformat())
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing Google result: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error searching Google News: {str(e)}")

        return results

search_service = SearchService() 