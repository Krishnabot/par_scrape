# Scraping Guide: Golf & Ski Resorts

This guide explains how to use the "Smart Scraper" tools to extract data from golf course and ski resort websites, and how to extend the functionality to capture more information.

## 0. Prerequisites

**CRITICAL**: You must set your Google Gemini API key for the extraction to work.
Add this line to your `.env` file in the root directory:

```bash
GOOGLE_API_KEY=your_api_key_here
```

Or execute it in your terminal before running the scripts:

```bash
export GOOGLE_API_KEY=your_api_key_here
```

## 1. How to Scrape Data

We have two dedicated scripts for scraping, one for each venue type. **You must provide a target URL.**

### Golf Courses
Use `run_golf_scrape.sh` to scrape golf course websites (pricing, dress code, access, etc.).

```bash
./run_golf_scrape.sh "https://ibarakicc.com/"
```

### Ski Resorts
Use `run_ski_scrape.sh` to scrape ski resort websites (lift ticket prices, season dates, rentals, etc.).

```bash
./run_ski_scrape.sh "https://brocken.jp/"
```

---

## 2. How It Works

The "Smart Scraper" (`src/par_scrape/smart_scraper.py`) follows these steps:
1.  **Visits the Main Page**: Fetches the content of the URL you provided.
2.  **Analyzes Links**: Looks for links to sub-pages containing specific keywords (e.g., "price", "access", "rule" for golf; "lift", "rental" for ski).
3.  **Crawls Relevant Pages**: Visits only the most important sub-pages (limit ~15) to gather detailed info without crawling the entire site.
4.  **Aggregates & Extracts**: Combines all text found and sends it to Google Gemini AI to extract structured data into JSON.

---

## 3. How to Extract More Data

If you need to get *more* data fields or change *what* pages are visited, you need to tweak two main files:

### A. To Find More Sub-Pages (Crawling Logic)

If the scraper is missing important pages (e.g., it's not visiting the "Restaurant" page), update the keywords in **`src/par_scrape/smart_scraper.py`**.

*   **For Golf**: Edit the `KEYWORDS_GOLF` list.
*   **For Ski**: Edit the `KEYWORDS_SKI` list.

```python
# Example: Adding "restaurant" and "menu" to golf keywords
KEYWORDS_GOLF = [
    "course", "layout", "slope", "price", "fee", "ticket", 
    "access", "map", "info", "guide", "rule", "dress", 
    "restaurant", "menu", "lunch", # <-- Added terms
    "施設", "料金", "アクセス", ...
]
```

### B. To Extract More Fields (AI Prompt)

If the scraper visits the right pages but doesn't save specific info (e.g., you want to extract "Sauna Availability"), you need to update the Extraction Script.

*   **For Golf**: Edit **`src/par_scrape/extract_golf_data.py`**
*   **For Ski**: Edit **`src/par_scrape/extract_ski_data.py`**

**Steps:**
1.  Open the file (e.g., `extract_ski_data.py`).
2.  Locate the `prompt` variable (the long string sent to the AI).
3.  Add your new field to the **Target JSON Schema** description.

```python
    Target JSON Schema:
    {
      "name": "Resort Name",
      ...
      "sauna_available": true/false,  # <-- New field
      "sauna_temp": "Temperature of sauna if mentioned", # <-- New field
      ...
    }
```

4.  **Important**: The AI will automatically try to find this new info in the aggregated text next time you run the script.
