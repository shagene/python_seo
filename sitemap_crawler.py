# sitemap_crawler.py

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


def sanitize_url_for_directory(url):
    """
    Sanitize the URL to make it suitable for directory names.
    """
    return url.replace('//', '_').replace('/', '_').replace(':', '_').replace('?', '_').replace('&', '_').replace('=', '_')

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
    if len(set(corpus)) > 1:
        tfidf_matrix = vectorizer.fit_transform(corpus)
        keywords = vectorizer.get_feature_names_out()
        return keywords
    return []


def content_organization_strategy(sitemap_data, main_save_directory):
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

            if len([h for h in headings if h.lower() == 'h1']) > 1:
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

            # Create a subdirectory for this URL's analysis
            url_subdir = os.path.join(main_save_directory, sanitize_url_for_directory(url))
            os.makedirs(url_subdir, exist_ok=True)

            with open(os.path.join(url_subdir, 'content_organization_analysis.json'), 'w') as file:
                json.dump(result, file, indent=2)  # Save the individual result

            analysis_results.append(result)
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

    # Optionally, you can save the aggregated results to the main directory
    with open(os.path.join(main_save_directory, 'aggregated_content_organization_analysis.json'), 'w') as file:
        json.dump(analysis_results, file, indent=2)

    print("Content Organization Strategy Analysis completed and saved.")


def url_optimization_analysis(sitemap_data, keywords, main_save_directory):
    url_analysis_results = []
    for url in sitemap_data.keys():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            result = {
                "url": url,
                "title": soup.title.string if soup.title else "No title",
                "meta_description": soup.find("meta", attrs={"name": "description"})["content"] if soup.find("meta", attrs={"name": "description"}) else "No meta description",
                "keywords": [keyword.get_text() for keyword in soup.find_all("meta", attrs={"name": "keywords"})],
                "h1": [h1.get_text() for h1 in soup.find_all('h1')],
                "top_keywords": [keyword for keyword in keywords if keyword in soup.get_text()]
            }

            # Create a subdirectory for this URL's analysis
            url_subdir = os.path.join(main_save_directory, sanitize_url_for_directory(url))
            os.makedirs(url_subdir, exist_ok=True)

            with open(os.path.join(url_subdir, 'url_optimization_analysis.json'), 'w') as file:
                json.dump(result, file, indent=2)  # Save the individual result

            url_analysis_results.append(result)
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

    # Optionally, you can save the aggregated results to the main directory
    with open(os.path.join(main_save_directory, 'aggregated_url_optimization_analysis.json'), 'w') as file:
        json.dump(url_analysis_results, file, indent=2)

    print("URL Optimization Analysis completed and saved.")


def content_analysis_input(sitemap_data, main_save_directory):
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

                    # Create a subdirectory for this URL's analysis
                    url_subdir = os.path.join(main_save_directory, sanitize_url_for_directory(url))
                    os.makedirs(url_subdir, exist_ok=True)

                    with open(os.path.join(url_subdir, 'content_analysis_input.json'), 'w') as file:
                        json.dump(result, file, indent=2)  # Save the individual result

                    content_results.append(result)
                except (ValueError, ZeroDivisionError) as e:
                    print(f"Error processing URL {url}: {str(e)}")
            else:
                print(f"Skipped analysis for {url} due to empty content.")
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

    # Optionally, you can save the aggregated results to the main directory
    with open(os.path.join(main_save_directory, 'aggregated_content_analysis_input.json'), 'w') as file:
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


def crawl_website(url_to_crawl, max_depth):
    current_time = datetime.datetime.now()
    current_time_string = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    crawler = Crawler(url_to_crawl, max_depth=max_depth, max_threads=10, timeout=20)
    crawler.crawl()
    json_file_path = crawler.save_sitemap(url_to_crawl + "_" + "depth_" + str(max_depth) + "_" + current_time_string)
    main_save_directory = crawler.main_save_directory

    # Extracting keywords
    keywords = extract_keywords(crawler.sitemap)

    # Calling the analyze_sitemap function to generate visualizations
    analyze_sitemap(json_file_path)

    # Running URL Optimization Analysis
    url_optimization_analysis(crawler.sitemap, keywords, main_save_directory)

    # Running Content Organization Strategy Analysis
    content_organization_strategy(crawler.sitemap, main_save_directory)

    # Running Content Analysis Input
    content_analysis_input(crawler.sitemap, main_save_directory)

    # Load the saved sitemap
    with open(json_file_path, 'r') as file:
        sitemap_data = json.load(file)

    # For each URL in the sitemap (excluding the main URL to avoid re-analysis)
    for url in sitemap_data[url_to_crawl]:
        if url == url_to_crawl:
            continue
        print(f"Analyzing {url}...")
        # Create a sub-directory for this URL
        url_subdir = os.path.join(main_save_directory, sanitize_url_for_directory(url))
        os.makedirs(url_subdir, exist_ok=True)

        # Running URL Optimization Analysis
        url_optimization_analysis({url: []}, [], url_subdir)  # Empty list since we're not crawling deeper

        # Running Content Organization Strategy Analysis
        content_organization_strategy({url: []}, url_subdir)

        # Running Content Analysis Input
        content_analysis_input({url: []}, url_subdir)

    return crawler.sitemap, main_save_directory