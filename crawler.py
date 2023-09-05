# crawler.py

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import threading
import os
import json
from urls_utils import headers, sanitize_url_for_directory



class Crawler:
    def __init__(self, base_url, max_depth=2, max_threads=10, timeout=30):
        self.base_url = self.format_url(base_url)
        self.max_depth = max_depth
        self.max_threads = max_threads
        self.timeout = timeout
        self.visited_urls = []
        self.sitemap = {}
        self.lock = threading.Lock()
        self.main_save_directory = ""

    @staticmethod
    def format_url(url):
        if not url.startswith('http'):
            try:
                requests.head('https://' + url, timeout=5, headers=headers)
                return 'https://' + url
            except requests.RequestException:
                return 'http://' + url
        return url

    def visit_url(self, url, depth):
        with self.lock:
            if depth >= self.max_depth or url in self.visited_urls:
                return
            self.visited_urls.append(url)
            self.sitemap[url] = []

        try:
            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
        except (requests.RequestException, ValueError):
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        self.sitemap[url] = [link.get('href') for link in soup.find_all('a') if
                             link.get('href') and link.get('href').startswith('http')]

        for link in self.sitemap[url]:
            self.visit_url(link, depth + 1)

    def crawl(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_url = {executor.submit(self.visit_url, url, 0): url for url in [self.base_url]}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f"{url} generated an exception: {str(exc)}")
                else:
                    print(f"{url} page is {len(self.sitemap[url])} links long")
            return self.sitemap

    def save_sitemap(self):
        folder_name = sanitize_url_for_directory(self.base_url)
        self.main_save_directory = os.path.join(os.getcwd(), folder_name)
        os.makedirs(self.main_save_directory, exist_ok=True)
        valid_filepath = os.path.join(self.main_save_directory, 'sitemap.json')
        with open(valid_filepath, 'w') as file:
            file.write(json.dumps(self.sitemap, indent=2))
        print(f"Sitemap saved to: {valid_filepath}")
        return valid_filepath
