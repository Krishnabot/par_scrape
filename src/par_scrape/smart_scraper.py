import os
import sys
import time
import re
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import html2text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import extract_golf_data
import extract_ski_data

KEYWORDS_GOLF = [
    "course", "layout", "slope", "price", "fee", "ticket", 
    "access", "map", "info", "guide", "rule", "dress", 
    "施設", "料金", "アクセス", "コース", "概要", "案内"
]

KEYWORDS_SKI = [
    "course", "slope", "lift", "price", "fee", "ticket", 
    "access", "map", "info", "guide", "rule", "rental", "school", 
    "snow", "weather", "stay", "restaurant",
    "ゲレンデ", "コース", "リフト", "料金", "アクセス", "レンタル", 
    "スクール", "雪", "天気", "宿泊", "レストラン"
]

def normalize_url(base_url, link):
    if not link:
        return None
    if link.startswith("javascript:") or link.startswith("mailto:") or link.startswith("#") or link.startswith("tel:"):
        return None
    return urljoin(base_url, link)

def smart_scrape(start_url: str, venue_type: str = "golf"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = urlparse(start_url).netloc
    output_dir = Path(f"output/{timestamp}/{domain}_smart")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Smart Scrape for: {start_url} (Type: {venue_type})")
    print(f"Output directory: {output_dir}")

    target_keywords = KEYWORDS_SKI if venue_type == "ski" else KEYWORDS_GOLF
    
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
                    # Avoid identical URL
                    links.append(full_url.split('#')[0])
            
            links = list(set(links)) # Unique
            
            # filter reelevant links
            relevant_links = []
            for link in links:
                if link == start_url or link.rstrip('/') == start_url.rstrip('/'):
                    continue
                    
                # Check keywords in URL or link text? 
                if any(kw in link.lower() for kw in target_keywords):
                    # vis it a file?/ (pdf, jpg)
                    if not any(link.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip']):
                        relevant_links.append(link)
            
            # Priorities : Rule/Dress > Price/Fee > Access > Info
            # Priorities : Lift/Price > Access > Course > Rental (Ski)
            # Limit
            target_links = relevant_links[:15] # Crawl up to 15 pages
            
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
    print(f"Scraping complete. Running extraction for {venue_type}...")
    if venue_type == "ski":
        extract_ski_data.extract_data(str(output_dir))
    else:
        extract_golf_data.extract_data(str(output_dir))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Scraper for Golf and Ski Resorts")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("--type", choices=["golf", "ski"], default="golf", help="Venue type (default: golf)")
    
    args = parser.parse_args()
    smart_scrape(args.url, args.type)
