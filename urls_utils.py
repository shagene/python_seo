headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

def sanitize_url_for_directory(url):
    """
    Sanitize the URL to make it suitable for directory names.
    """
    return url.replace('//', '_').replace('/', '_').replace(':', '_').replace('?', '_').replace('&', '_').replace('=', '_')
