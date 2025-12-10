import os
import sys
import json
import time
from pathlib import Path
import google.generativeai as genai

def extract_data(input_path: str):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    
    # Use a model that supports JSON mode 
    model_name = 'gemini-flash-latest'
    try:
        model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
    except Exception:
        print(f"Failed to load {model_name}, trying gemini-pro")
        model = genai.GenerativeModel('gemini-pro')

    input_path_obj = Path(input_path)
    aggregated_text = ""
    
    if input_path_obj.is_file():
        try:
            aggregated_text = input_path_obj.read_text(encoding='utf-8')
            output_dir = input_path_obj.parent
        except Exception as e:
            print(f"Error reading raw data: {e}")
            sys.exit(1)
    elif input_path_obj.is_dir():
        print(f"Aggregating markdown files from {input_path}...")
        md_files = list(input_path_obj.rglob("*.md"))
        msg_parts = []
        for md_file in md_files:
            if md_file.name.startswith("extracted_data"):
                 continue
            try:
                content = md_file.read_text(encoding='utf-8')
                msg_parts.append(f"\n\n--- Source: {md_file.name} ---\n{content}")
            except Exception as e:
                print(f"Warning: Could not read {md_file}: {e}")
        
        aggregated_text = "".join(msg_parts)
        output_dir = input_path_obj
        if not aggregated_text:
            print("No markdown content found to extract from.")
            sys.exit(1)
    else:
        print(f"Error: Input path {input_path} does not exist.")
        sys.exit(1)

    prompt = """
    You are an expert data extractor. Your task is to extract structured SKI RESORT information from the provided text.
    The text may contain content from multiple pages. Aggregate information from all sources to fill the fields.
    
    Return a single JSON object with the following fields. If a field is not found, use null or false as appropriate, or empty string "" for text fields.
    
    Target JSON Schema:
    {
      "name": "Resort Name",
      "official_url": "Official website URL",
      "address": "Full Address",
      "postal_code": "Postal Code",
      "phone_number": "Phone Number",
      "english_website": true/false (true if English site/pages exist),
      "english_site_url": "URL of English site if available",
      "english_staff": true/false (true if explicitly mentioned),
      "credit_cards_accepted": true/false,
      "equipment_rental_available": true/false,
      "wifi_available": true/false,
      "adult_day_pass_price": integer (Standard adult 1-day lift ticket price, use null if not found),
      "lift_ticket_prices": ["Array of strings describing various ticket prices (e.g., '1 Day Adult: 5000 JPY', '4 Hours: ...')"],
      "price_notes": "Notes about pricing (e.g., senior discounts, early bird)",
      "price_updated_at": "YYYY-MM-DD" (if date is mentioned, else null),
      "season_info": "General season description (e.g., 'Dec to May')",
      "season_status": "Current status (Open/Closed) if mentioned",
      "season_open_date": "YYYY-MM-DD" (Estimated or explicit open date),
      "season_close_date": "YYYY-MM-DD" (Estimated or explicit close date),
      "news_items": [
        {
          "date": "YYYY-MM-DD",
          "title": "News Title",
          "content": "News Content summary"
        }
      ],
      "sources_checked": ["List of source filenames or URLs"]
    }

    Input Text:
    """ + aggregated_text

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            extracted_json = json.loads(response.text)
            
            output_file = output_dir / "extracted_data_custom.json"
            output_file.write_text(json.dumps(extracted_json, indent=4, ensure_ascii=False), encoding='utf-8')
            print(f"Successfully saved extracted data to {output_file}")
            return
            
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit exceeded. Waiting 20 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(20)
            else:
                print(f"Error during extraction: {e}")
                return
    print("Failed to extract data after retries.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_ski_data.py <path_to_raw_data_or_dir>")
        sys.exit(1)
    extract_data(sys.argv[1])
