from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import datetime
import threading
import os
import json
from urllib.parse import urlparse
from sitemap_visualizations import analyze_sitemap
from sklearn.feature_extraction.text import TfidfVectorizer
from textatistic import Textatistic

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

def generate_article_json_ld(title, author, date_published, image_url, description):
    """
    Generate a generic JSON-LD structured data snippet for an article.
    """
    return {
        "@context": "http://schema.org",
        "@type": "Article",
        "headline": title,
        "author": {
            "@type": "Person",
            "name": author
        },
        "datePublished": date_published,
        "image": image_url,
        "articleBody": description,
        "publisher": {
            "@type": "Organization",
            "name": "Unknown Publisher",
            "logo": {
                "@type": "ImageObject",
                "url": "https://example.com/logo.png"
            }
        }
    }


# Function to extract top 10 keywords using TF-IDF
def extract_keywords(sitemap_data):
    corpus = []
    for url in sitemap_data.keys():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            corpus.append(text)
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

    vectorizer = TfidfVectorizer(stop_words='english', max_features=10)

    # Check if the corpus contains meaningful content
    if len(set(corpus)) > 1:
        tfidf_matrix = vectorizer.fit_transform(corpus)
        keywords = vectorizer.get_feature_names_out()
        return keywords
    return []


# Content Organization Strategy
def content_organization_strategy(sitemap_data, save_directory):
    analysis_results = []
    for url in sitemap_data.keys():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            headings = [heading.text.strip() for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
            result = {
                "url": url,
                "headings": headings,
                "number_of_sections": len(soup.find_all(['section'])),
                "recommendations": []
            }
            if headings.count('h1') > 1:
                result["recommendations"].append("Avoid using multiple H1 tags.")

            # Check for Schema Markup
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            if scripts:
                result["schema_detected"] = True
            else:
                result["schema_detected"] = False
                title = soup.find('title').get_text() if soup.find('title') else ""
                description_tag = soup.find('meta', attrs={'name': 'description'})
                description = description_tag['content'] if description_tag else ""
                # Suggest adding structured data for an article
                article_data = generate_article_json_ld(title, "Unknown Author", "Unknown Date", "Unknown Image URL",
                                                        description)
                json_ld_script = f'<script type="application/ld+json">{json.dumps(article_data, indent=2)}</script>'
                result["schema_suggestion"] = json_ld_script

            analysis_results.append(result)
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

    with open(os.path.join(save_directory, 'content_organization_analysis.json'), 'w') as file:
        json.dump(analysis_results, file, indent=2)

    print("Content Organization Strategy Analysis completed and saved.")


# Content Analysis Input
def content_analysis_input(sitemap_data, save_directory):
    content_results = []
    for url in sitemap_data.keys():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()

            # Remove words that are longer than 100 characters
            text_content = " ".join(word if len(word) <= 100 else "" for word in text_content.split())

            # Check if the text content is not empty
            if text_content.strip():
                try:
                    text_stats = Textatistic(text_content)
                    readability_score = text_stats.flesch_score

                    result = {
                        "url": url,
                        "readability_score": readability_score,
                        "interpretation": "",
                        "recommendations": []
                    }

                    if readability_score < 0:
                        result["interpretation"] = "Extremely difficult to read."
                        result["recommendations"].append("Check for complex sentences and lack of punctuation.")
                        result["recommendations"].append("Consider simplifying the language.")
                    elif readability_score < 30:
                        result["interpretation"] = "Difficult to read."
                        result["recommendations"].append("Simplify sentences and use more common words.")
                    elif readability_score < 60:
                        result["interpretation"] = "Moderately difficult to read."
                        result["recommendations"].append("Consider breaking up long sentences.")
                    else:
                        result["interpretation"] = "Easy to read."

                    content_results.append(result)
                except (ValueError, ZeroDivisionError) as e:
                    print(f"Error processing URL {url}: {str(e)}")
            else:
                print(f"Skipped analysis for {url} due to empty content.")
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

    with open(os.path.join(save_directory, 'content_analysis_input.json'), 'w') as file:
        json.dump(content_results, file, indent=2)

    print("Content Analysis Input completed and saved.")


class Crawler:
    def __init__(self, base_url, max_depth=2, max_threads=10, timeout=30):
        self.base_url = self.format_url(base_url)
        self.max_depth = max_depth
        self.max_threads = max_threads
        self.timeout = timeout
        self.visited_urls = []
        self.sitemap = {}
        self.lock = threading.Lock()

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

    def save_sitemap(self, filepath):
        folder_name = filepath.replace('//', '_').replace('/', '_').replace(':', '_')
        save_directory = os.path.join(os.getcwd(), folder_name)
        os.makedirs(save_directory, exist_ok=True)
        valid_filepath = os.path.join(save_directory, 'sitemap.json')
        with open(valid_filepath, 'w') as file:
            file.write(json.dumps(self.sitemap, indent=2))
        print(f"Sitemap saved to: {valid_filepath}")
        return valid_filepath


# URL Optimization Analysis
def url_optimization_analysis(sitemap_data, keywords, save_directory):
    analysis_results = []
    for url in sitemap_data.keys():
        parsed_url = urlparse(url)
        path = parsed_url.path
        result = {
            "url": url,
            "contains_keywords": any(keyword in path for keyword in keywords),
            "use_hyphens": "-" in path,
            "url_length": len(path),
            "recommendations": []
        }
        if not result["contains_keywords"]:
            result["recommendations"].append("Include target keywords in the URL.")
        if "_" in path:
            result["recommendations"].append("Use hyphens instead of underscores.")
        if len(path) > 100:
            result["recommendations"].append("Shorten the URL length.")

        analysis_results.append(result)

    with open(os.path.join(save_directory, 'url_optimization_analysis.json'), 'w') as file:
        json.dump(analysis_results, file, indent=2)

    print("URL Optimization Analysis completed and saved.")


def crawl_website(url_to_crawl, max_depth):
    current_time = datetime.datetime.now()
    current_time_string = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    crawler = Crawler(url_to_crawl, max_depth=max_depth, max_threads=10, timeout=20)
    crawler.crawl()
    json_file_path = crawler.save_sitemap(url_to_crawl + "_" + "depth_" + str(max_depth) + "_" + current_time_string)
    save_directory = os.path.dirname(json_file_path)

    # Extracting keywords
    keywords = extract_keywords(crawler.sitemap)

    # Calling the analyze_sitemap function to generate visualizations
    analyze_sitemap(json_file_path)

    # Running URL Optimization Analysis
    url_optimization_analysis(crawler.sitemap, keywords, save_directory)

    # Running Content Organization Strategy Analysis
    content_organization_strategy(crawler.sitemap, save_directory)

    # Running Content Analysis Input
    content_analysis_input(crawler.sitemap, save_directory)

    return crawler.sitemap, save_directory
