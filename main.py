# main.py
import json
import os
from crawler import Crawler
from analysis_functions import extract_keywords, url_optimization_analysis, content_organization_strategy, \
    content_analysis_input
import requests
import random
from urllib.parse import urlparse

# Dynamic User-Agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/83.0.478.37"
]


def get_random_user_agent():
    return random.choice(USER_AGENTS)


COMMON_TLDs = ['.com', '.org', '.net', '.gov', '.edu', '.gg']


def validate_url(url):
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    if not any(tld in parsed.netloc for tld in COMMON_TLDs):
        return False
    return True


def main():
    # Get input from user
    url_to_crawl = input("Please enter the URL to crawl: ")

    # Validate the entered URL
    while not validate_url(url_to_crawl):
        print("Invalid URL. Please check and enter again.")
        url_to_crawl = input("Please enter the URL to crawl: ")

    # Ensure the URL has the correct scheme (http:// or https://)
    if not url_to_crawl.startswith(('http://', 'https://')):
        user_agent = get_random_user_agent()
        headers = {"User-Agent": user_agent}
        try:
            response = requests.head('https://' + url_to_crawl, headers=headers)
            if response.status_code < 400:  # if the server responds okay
                url_to_crawl = 'https://' + url_to_crawl
            else:
                url_to_crawl = 'http://' + url_to_crawl
        except requests.ConnectionError:
            url_to_crawl = 'http://' + url_to_crawl

    max_depth = int(input("Please enter the maximum depth to crawl (e.g., 2): "))

    # Crawl the website and get sitemap
    crawler = Crawler(url_to_crawl, max_depth)
    sitemap_data = crawler.crawl()

    # Save the sitemap
    sitemap_filepath = crawler.save_sitemap()
    main_save_directory = os.path.dirname(sitemap_filepath)

    # Extracting keywords
    keywords = extract_keywords(sitemap_data)

    # Running URL Optimization Analysis
    url_optimization_analysis(sitemap_data, keywords, main_save_directory)

    # Running Content Organization Strategy Analysis
    content_organization_strategy(sitemap_data, main_save_directory)

    # Running Content Analysis Input
    content_analysis_input(sitemap_data, main_save_directory)

    print(f"Sitemap saved to: {sitemap_filepath}")


if __name__ == '__main__':
    main()
