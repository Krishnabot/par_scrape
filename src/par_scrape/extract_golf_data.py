import os
import sys
import json
import glob
from pathlib import Path
import google.generativeai as genai
from typing import Optional

def extract_data(input_path: str):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    
    # List models to debug
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

    # Use a model that supports JSON mode if possible
    model_name = 'gemini-flash-latest'
    try:
        model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
    except Exception:
        print(f"Failed to load {model_name}, trying gemini-pro")
        model = genai.GenerativeModel('gemini-pro')

    input_path_obj = Path(input_path)
    aggregated_text = ""
    
    if input_path_obj.is_file():
         # Single file mode (legacy support or direct file target)
        try:
            aggregated_text = f"--- Source: {input_path_obj.name} ---\n" + input_path_obj.read_text(encoding='utf-8')
            output_dir = input_path_obj.parent
        except Exception as e:
            print(f"Error reading file {input_path}: {e}")
            sys.exit(1)
    elif input_path_obj.is_dir():
        print(f"Aggregating markdown files from {input_path}...")
        md_files = list(input_path_obj.rglob("*.md"))
        msg_parts = []
        for md_file in md_files:
            if md_file.name.startswith("extracted_data") or md_file.name.endswith("-raw.md"):
                 pass
            
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

    print(f"Total aggregated content length: {len(aggregated_text)} characters")

    prompt = """
    You are an expert data extractor. Your task is to extract structured golf course information from the provided text.
    The text may contain content from multiple pages of the same golf course website. Aggregate information from all sources to fill the fields.
    
    Return a single JSON object with the following fields. If a field is not found, use an empty string "".
    
    Fields:
    - name: Name of the golf course
    - official_url: Official website URL (prefer the main homepage)
    - prefecture_name_jp: Prefecture name in Japanese
    - address: Full address
    - postal_code: Postal code
    - nearest_station: Nearest train station
    - weekday_price_min: Minimum weekday price (integer)
    - weekday_price_max: Maximum weekday price (integer)
    - weekend_price_min: Minimum weekend price (integer)
    - weekend_price_max: Maximum weekend price (integer)
    - price_notes: Notes about pricing (e.g., includes lunch, caddy fee, seasonal rates)
    - price_updated_at: Date when price info was updated
    - english_staff: specific mention of English speaking staff availability (true/false)
    - english_website: availability of English website (true/false)
    - english_site_url: URL of the English website
    - credit_cards_accepted: List of accepted credit cards or boolean
    - equipment_rental_available: Availability of equipment rental
    - foreigner_friendly: specific mention of being foreigner friendly
    - accessible_by_train: Availability of train access
    - shuttle_bus_available: Availability of shuttle bus
    - extra_info: Any other relevant information (dress code, cancellation fee, etc.)
    - opening_hours: Opening hours
    - par: Total par
    - holes: Total number of holes
    - yardage_total: Total yardage
    - news_items: List of recent news items
    - sources_checked: List of source URLs or filenames used

    Input Text:
    """ + aggregated_text

    import time
    
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
                if 'response' in locals() and hasattr(response, 'text'):
                    print(f"Response text: {response.text}")
                return
    print("Failed to extract data after retries.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        output_base = Path("output")
        if output_base.exists():
            timestamp_dirs = sorted([d for d in output_base.iterdir() if d.is_dir()], key=os.path.getmtime, reverse=True)
            if timestamp_dirs:
                latest_dir = timestamp_dirs[0]
                print(f"Auto-detected latest crawl directory: {latest_dir}")
                extract_data(str(latest_dir))
                sys.exit(0)
        
        print("Usage: python extract_golf_data.py <path_to_raw_data.md_or_directory>")
        sys.exit(1)
    else:
        extract_data(sys.argv[1])
