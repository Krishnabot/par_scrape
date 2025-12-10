#!/bin/bash

if [ -z "$1" ]; then
  echo "You should enter a ski resort web site to scrap"
  exit 1
fi
URL=$1

# Google API Key from  .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi
echo "Starting Ski Resort Scrape for URL: $URL"

export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uv run python3 src/par_scrape/smart_scraper.py "$URL" --type ski
