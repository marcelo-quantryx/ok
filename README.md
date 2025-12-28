# OK Mobility Car Scraper

A Python scraper to extract available car information from OK Mobility subscription pages.

## Features

- Scrapes car availability data from OK Mobility website
- Extracts detailed information including:
  - Car name and category
  - SIPP code
  - Seats, transmission, doors
  - Pricing (original and discounted)
  - Duration options
  - Vehicle images
  - Special badges (e.g., Plug-in Hybrid)
- Works with both local HTML files and live URLs
- Exports data to JSON format

## Installation

This project uses `uv` for dependency management:

```bash
# Install dependencies
uv pip install -e .

# Or install dependencies in a virtual environment
uv venv
source .venv/bin/activate  # On Linux/macOS
uv pip install -e .
```

## Usage

### Basic usage with local HTML file:

```bash
python scraper.py
```

This will:
1. Read the `2025-12-27.html` file
2. Extract all available cars
3. Display the results in the terminal
4. Save the data to `cars_availability.json`

### Scraping from URL:

Edit `scraper.py` and uncomment the URL scraping section in the `main()` function, then run:

```bash
python scraper.py
```

### Using as a library:

```python
from scraper import OKMobilityScraper

scraper = OKMobilityScraper()

# From URL
cars = scraper.scrape_from_url("https://okmobility.com/en/subscription/...")

# From file
cars = scraper.scrape_from_file("2025-12-27.html")

# Process the data
for car in cars:
    print(f"{car['name']}: €{car['pricing']['discounted_price']}/month")
```

## Output Format

The scraper returns a list of dictionaries with the following structure:

```json
{
  "sipp_code": "EMMS",
  "name": "Peugeot 208",
  "category": "Urban",
  "seats": 5,
  "equipment": {
    "seats": "5 Seats",
    "transmission": "Manual",
    "doors": "5 Doors"
  },
  "pricing": {
    "original_price": 414.0,
    "discounted_price": 373.0
  },
  "duration_options": "3, 4, 5, 6, 7, 8, 9 months",
  "images": [...],
  "booking_url": "/en/subscription/booking/availability/...",
  "badges": []
}
```

## Dependencies

- beautifulsoup4 - HTML parsing
- requests - HTTP requests
- lxml - Fast HTML parser

## License

MIT
