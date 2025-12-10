import os
import sys
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import html2text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from extract_golf_data import extract_data

KEYWORDS = [
    "course", "layout", "slope", "price", "fee", "ticket", 
    "access", "map", "info", "guide", "rule", "dress", 
    "施設", "料金", "アクセス", "コース", "概要", "案内" # Japaneese keywords
]

def normalize_url(base_url, link):
    if not link:
        return None
    if link.startswith("javascript:") or link.startswith("mailto:") or link.startswith("#"):
        return None
    return urljoin(base_url, link)

def smart_scrape(start_url: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = urlparse(start_url).netloc
    output_dir = Path(f"output/{timestamp}/{domain}_smart")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Smart Scrape for: {start_url}")
    print(f"Output directory: {output_dir}")

    h = html2text.HTML2Text()
    h.ignore_links = False
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # fetch Main Page
        print(f"Fetching main page: {start_url}")
        try:
            page.goto(start_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            content = page.content()
            
            # save Main Page
            main_md = h.handle(content)
            (output_dir / "main.md").write_text(f"--- Source: {start_url} ---\n{main_md}", encoding='utf-8')
            
            # find Sub-pages
            soup = BeautifulSoup(content, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                full_url = normalize_url(start_url, a['href'])
                if full_url and urlparse(full_url).netloc == domain:
                    links.append(full_url)
            
            links = list(set(links)) # Unique
            
            # filter reelevant links
            relevant_links = []
            for link in links:
                if link == start_url:
                    continue
                    
                # Check keywords in URL or link text? 
                # meaningful_part = ?
                # Check entire URL for keyword match
                if any(kw in link.lower() for kw in KEYWORDS):
                    # vis it a file?/ (pdf, jpg)
                    if not any(link.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip']):
                        relevant_links.append(link)
            
            # Priorities : Rule/Dress > Price/Fee > Access > Info
            # Limit
            target_links = relevant_links[:10] # Crawl up to 10  pages
            
            print(f"Found {len(relevant_links)} relevant links. Crawling top {len(target_links)}: {target_links}")
            
            #  Sub-pages
            for i, link in enumerate(target_links):
                print(f"Fetching sub-page ({i+1}/{len(target_links)}): {link}")
                try:
                    page.goto(link, timeout=30000)
                    page.wait_for_load_state("domcontentloaded") 
                    sub_content = page.content()
                    
                    sub_md = h.handle(sub_content)
                    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', link.split(domain)[-1])[:50]
                    (output_dir / f"sub_{i}_{safe_name}.md").write_text(f"--- Source: {link} ---\n{sub_md}", encoding='utf-8')
                    
                    time.sleep(1) 
                except Exception as e:
                    print(f"Failed to fetch {link}: {e}")
                    
        except Exception as e:
            print(f"Critical error scraping main page: {e}")
        finally:
            browser.close()

    # Extract
    print("Scraping complete. Running extraction...")
    extract_data(str(output_dir))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smart_scraper.py <url>")
        sys.exit(1)
    
    smart_scrape(sys.argv[1])
