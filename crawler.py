import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

def is_valid_url(url, base_domain):
    parsed = urlparse(url)
    return parsed.netloc == base_domain and parsed.scheme in ['http', 'https']

def extract_text_from_html(html_content, base_url, base_domain):
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Remove unwanted elements
    for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'img', 'iframe', 'noscript']):
        tag.decompose()
    
    # Extract title
    title = soup.title.string if soup.title else ""
    
    # Extract headings
    headings = []
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        headings.append(h.get_text().strip())
    
    # Extract visible text
    text = soup.get_text(separator=' ', strip=True)
    
    # Extract links
    links = []
    for a in soup.find_all('a', href=True):
        link = urljoin(base_url, a['href'])
        if is_valid_url(link, base_domain):
            links.append(link)
    
    return {
        'title': title,
        'headings': headings,
        'text': text,
        'links': links
    }

def crawl_website(base_url, max_depth=2, progress_callback=None):
    base_domain = urlparse(base_url).netloc
    visited = set()
    to_visit = [(base_url, 0)]
    documents = []
    
    while to_visit:
        current_url, depth = to_visit.pop(0)
        if current_url in visited or depth > max_depth:
            continue
        visited.add(current_url)
        
        if progress_callback:
            progress_callback(len(visited), len(to_visit), current_url)
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(current_url, timeout=10, headers=headers, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                continue
            
            current_url = response.url  # Handle redirects
            data = extract_text_from_html(response.text, current_url, base_domain)
            data['url'] = current_url
            documents.append(data)
            
            if depth < max_depth:
                for link in data['links']:
                    if link not in visited:
                        to_visit.append((link, depth + 1))
            
            time.sleep(1)  # Polite crawling
        
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")
    
    return documents