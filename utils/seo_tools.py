import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import pandas as pd
from typing import Optional, Dict, List
import time
import re
from collections import Counter
from utils.config import Config

class FreeSEOTools:
    @staticmethod
    def extract_keywords(text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text using TF-IDF like approach"""
        words = re.findall(r'\b\w{3,}\b', text.lower())
        stop_words = set([
            'the', 'and', 'of', 'to', 'in', 'is', 'it', 'that', 'for', 
            'you', 'was', 'on', 'are', 'with', 'as', 'at', 'be', 
            'this', 'have', 'from', 'or', 'an', 'by', 'not'
        ])
        filtered_words = [word for word in words if word not in stop_words and not word.isdigit()]
        
        # Simple scoring: frequency * length
        word_scores = {word: count * len(word) for word, count in Counter(filtered_words).items()}
        return sorted(word_scores.keys(), key=lambda x: word_scores[x], reverse=True)[:top_n]

    @staticmethod
    def get_google_search_results(query: str, num_results: int = 5) -> List[Dict]:
        """Get Google search results using Custom Search JSON API"""
        if not Config.GOOGLE_CSE_ID:
            return []
            
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': Config.GOOGLE_API_KEY,
                'cx': Config.GOOGLE_CSE_ID,
                'q': query,
                'num': num_results
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json().get('items', [])
            return []
        except Exception as e:
            print(f"Error fetching Google results: {str(e)}")
            return []

    @staticmethod
    def analyze_competitors(query: str, num_competitors: int = 3) -> pd.DataFrame:
        """Analyze top search results for a query"""
        results = FreeSEOTools.get_google_search_results(query, num_competitors)
        competitor_data = []
        
        for item in results:
            try:
                url = item.get('link', '')
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title = soup.title.string if soup.title else "No title"
                h1 = soup.find('h1').get_text() if soup.find('h1') else "No H1"
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                meta_desc = meta_desc['content'] if meta_desc else "No meta description"
                word_count = len(soup.get_text().split())
                
                competitor_data.append({
                    'URL': url,
                    'Title': title,
                    'H1': h1,
                    'Meta Description': meta_desc,
                    'Word Count': word_count,
                    'Rank': item.get('rank', '')
                })
                
                time.sleep(2)  # Be polite with requests
                
            except Exception as e:
                print(f"Error analyzing {url}: {str(e)}")
                continue
                
        return pd.DataFrame(competitor_data)

    @staticmethod
    def calculate_readability(text: str) -> Dict:
        """Calculate basic readability metrics"""
        sentences = re.split(r'[.!?]', text)
        words = text.split()
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_word_length': round(avg_word_length, 1),
            'reading_level': 'College' if avg_sentence_length > 20 else 'High School' if avg_sentence_length > 15 else 'Easy'
        }

    @staticmethod
    def generate_meta_tags(title: str, description: str, keywords: List[str]) -> str:
        """Generate HTML meta tags for SEO"""
        keywords_str = ', '.join(keywords)
        return f"""
        <title>{title}</title>
        <meta name="description" content="{description}">
        <meta name="keywords" content="{keywords_str}">
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="{description}">
        """