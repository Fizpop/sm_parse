import logging
from urllib.parse import urlparse
import tldextract
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainAnalyzer:
    def __init__(self):
        self.known_media_tlds = {
            'news', 'media', 'press', 'com', 'org', 'net', 'info',
            'ua', 'uk', 'us', 'eu', 'ru', 'by', 'kz'
        }
        
    def extract_clean_domain(self, url: str) -> str:
        """
        Витягує та нормалізує домен з URL.
        Приклад: https://www.example.com/path -> example.com
        """
        try:
            # Використовуємо tldextract для правильної обробки доменів
            extracted = tldextract.extract(url)
            # Збираємо домен без субдоменів
            domain = f"{extracted.domain}.{extracted.suffix}"
            return domain.lower()
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {str(e)}")
            return ""
            
    def analyze_domain(self, url: str) -> Dict:
        """
        Аналізує домен та повертає його характеристики
        """
        try:
            extracted = tldextract.extract(url)
            domain_info = {
                'domain': f"{extracted.domain}.{extracted.suffix}",
                'subdomain': extracted.subdomain if extracted.subdomain else None,
                'tld': extracted.suffix,
                'is_media_tld': extracted.suffix in self.known_media_tlds,
                'is_known_media': self._is_known_media_domain(f"{extracted.domain}.{extracted.suffix}"),
                'language': self._detect_language(url),
                'category': self._detect_category(url),
                'analyzed_at': None  # Буде встановлено при збереженні
            }
            return domain_info
        except Exception as e:
            logger.error(f"Error analyzing domain {url}: {str(e)}")
            return {}
            
    def _is_known_media_domain(self, domain: str) -> bool:
        """
        Перевіряє чи є домен відомим медіа-ресурсом
        """
        known_media_patterns = [
            r'news\.',
            r'media\.',
            r'press\.',
            r'tv\.',
            r'radio\.',
            r'gazette\.',
            r'times\.',
            r'post\.'
        ]
        return any(re.search(pattern, domain.lower()) for pattern in known_media_patterns)
            
    def _detect_language(self, url: str) -> Optional[str]:
        """
        Визначає основну мову сайту
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Спробуємо знайти мову в HTML тегах
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                return html_tag.get('lang').split('-')[0]
                
            # Спробуємо знайти мету-теги з мовою
            meta_lang = soup.find('meta', attrs={'http-equiv': 'content-language'})
            if meta_lang:
                return meta_lang.get('content', '').split('-')[0]
                
            return None
        except Exception as e:
            logger.error(f"Error detecting language for {url}: {str(e)}")
            return None
            
    def _detect_category(self, url: str) -> Optional[str]:
        """
        Визначає категорію сайту
        """
        categories = {
            'news': ['news', 'latest', 'breaking', 'headlines'],
            'blog': ['blog', 'article', 'post'],
            'corporate': ['about', 'company', 'corporate'],
            'social': ['social', 'community', 'network'],
            'government': ['gov', 'government', 'ministry'],
            'education': ['edu', 'education', 'university', 'school']
        }
        
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            
            for category, keywords in categories.items():
                if any(keyword in path for keyword in keywords):
                    return category
                    
            return 'other'
        except Exception as e:
            logger.error(f"Error detecting category for {url}: {str(e)}")
            return None

domain_analyzer = DomainAnalyzer() 