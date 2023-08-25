import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
import googlesearch
import json

# Ensure you have the necessary NLTK resources downloaded.
nltk.download('stopwords')
nltk.download('punkt')


def generate_article_json_ld(title, author, publish_date, image_url, description):
    """Generate structured data for an article."""
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "author": author,
        "datePublished": publish_date,
        "image": image_url,
        "description": description
    }
    return json_ld


def seo_analysis(url):
    results = {
        'keywords': [],
        'good': [],
        'bad': [],
        'schema_suggestion': None
    }

    # Fetch the content of the webpage
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        results['bad'].append("Error: Unable to access the website.")
        return results

    soup = BeautifulSoup(response.content, 'html.parser')

    # Check for title and description
    title = soup.find('title').get_text() if soup.find('title') else None
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag['content'] if description_tag else None

    if title:
        results['good'].append("Title Exists! Great!")
    else:
        results['bad'].append("Title does not exist! Add a Title")

    if description:
        results['good'].append("Description Exists! Great!")
    else:
        results['bad'].append("Description does not exist! Add a Meta Description")

    # Extract heading information
    if not soup.find('h1'):
        results['bad'].append("No H1 found!")

    # Check images for alt attributes
    for img in soup.find_all('img'):
        if not img.get('alt'):
            results['bad'].append(f"No Alt attribute for image: {img.get('src')}")

    # Keyword analysis
    body_text = soup.find('body').text
    words = [word.lower() for word in word_tokenize(body_text)]
    stopwords = nltk.corpus.stopwords.words('english')
    filtered_words = [word for word in words if word not in stopwords and word.isalpha()]
    freq_dist = nltk.FreqDist(filtered_words)
    results['keywords'] = freq_dist.most_common(10)

    # Check Google Search rank for top keyword
    search_results = list(googlesearch.search(results['keywords'][0][0], num_results=10))
    if url in search_results:
        results['good'].append(
            f"The site appears in the top 10 Google results for its top keyword: {results['keywords'][0][0]}!")
    else:
        results['bad'].append(
            f"The site does not appear in the top 10 Google results for its top keyword: {results['keywords'][0][0]}.")

    # Check for Schema Markup
    scripts = soup.find_all('script', {'type': 'application/ld+json'})
    if scripts:
        results['good'].append("Schema markup detected!")
    else:
        results['bad'].append("No schema markup detected.")
        # Suggest adding structured data for an article
        article_data = generate_article_json_ld(title, "Unknown Author", "Unknown Date", "Unknown Image URL",
                                                description)
        json_ld_script = f'<script type="application/ld+json">{json.dumps(article_data, indent=2)}</script>'
        results['schema_suggestion'] = json_ld_script

    return results

    url_to_analyze = sys.argv[1] if len(sys.argv) > 1 else default_url
    results = seo_analysis(url_to_analyze)
    print(json.dumps(results, indent=2))