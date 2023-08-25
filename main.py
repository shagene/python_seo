# main.py

import json
import os
from sitemap_crawler import crawl_website
from seo_analyzer import seo_analysis
import requests

def main():
    # Get input from user
    url_to_crawl = input("Please enter the URL to crawl: ")

    # Ensure the URL has the correct scheme (http:// or https://)
    if not url_to_crawl.startswith(('http://', 'https://')):
        try:
            response = requests.head('https://' + url_to_crawl)
            if response.status_code < 400:  # if the server responds okay
                url_to_crawl = 'https://' + url_to_crawl
            else:
                url_to_crawl = 'http://' + url_to_crawl
        except requests.ConnectionError:
            url_to_crawl = 'http://' + url_to_crawl

    max_depth = int(input("Please enter the maximum depth to crawl (e.g., 2): "))

    # Crawl the website and get sitemap
    sitemap_data, save_directory = crawl_website(url_to_crawl, max_depth)

    # Analyze the sitemap for SEO
    seo_results = seo_analysis(url_to_crawl)

    # Save the SEO results
    with open(os.path.join(save_directory, 'seo_analysis_results.json'), 'w') as file:
        json.dump(seo_results, file, indent=2)
    print(f"SEO Analysis Results saved to: {os.path.join(save_directory, 'seo_analysis_results.json')}")


if __name__ == '__main__':
    main()
