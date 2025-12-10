#!/bin/bash

# Default URL (Wikipedia List of Golf Courses in Japan)
URL=${1:-"https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E3%81%AE%E3%82%B4%E3%83%AB%E3%83%95%E5%A0%B4%E4%B8%80%E8%A6%A7"}

# Export the Google API Key from  .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi
echo "Starting Golf Course Scrape for URL: $URL"

# Run the smart scraper
echo "Running smart scraper for URL: $URL"
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uv run python3 src/par_scrape/smart_scraper.py "$URL"

# uv run python3 -m src.par_scrape \
#   --url "$URL" \
#   --output-format json \
#   --output-format markdown \
#   --extraction-prompt "src/par_scrape/golf_course_extraction_prompt.md" \
#   --fields "name" \
#   --fields "official_url" \
#   --fields "prefecture_name_jp" \
#   --fields "address" \
#   --fields "postal_code" \
#   --fields "nearest_station" \
#   --fields "weekday_price_min" \
#   --fields "weekday_price_max" \
#   --fields "weekend_price_min" \
#   --fields "weekend_price_max" \
#   --fields "price_notes" \
#   --fields "price_updated_at" \
#   --fields "english_staff" \
#   --fields "english_website" \
#   --fields "english_site_url" \
#   --fields "credit_cards_accepted" \
#   --fields "equipment_rental_available" \
#   --fields "foreigner_friendly" \
#   --fields "accessible_by_train" \
#   --fields "shuttle_bus_available" \
#   --fields "extra_info" \
#   --fields "opening_hours" \
#   --fields "par" \
#   --fields "holes" \
#   --fields "yardage_total" \
#   --fields "news_items" \
#   --fields "sources_checked" \
#   --ai-provider Gemini \
#   --model "gemini-1.5-flash" \
#   --crawl-type domain \
#   --crawl-max-pages 50 \
#   --output-folder "./output/golf_courses" \
#   --display-output md

# echo "Running custom extraction script..."
# uv run python3 src/par_scrape/extract_golf_data.py
