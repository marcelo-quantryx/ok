#!/usr/bin/env python3
"""
OK Mobility Car Scraper
Extracts available car information from OK Mobility subscription pages
"""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests
import json
import re


class OKMobilityScraper:
    """Scraper for OK Mobility car availability"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def scrape_from_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape car data from a URL
        
        Args:
            url: The OK Mobility availability URL
            
        Returns:
            List of dictionaries containing car information
        """
        response = self.session.get(url)
        response.raise_for_status()
        return self.parse_html(response.text)
    
    def scrape_from_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Scrape car data from a local HTML file
        
        Args:
            filepath: Path to the HTML file
            
        Returns:
            List of dictionaries containing car information
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return self.parse_html(html_content)
    
    def parse_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content and extract car information
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            List of dictionaries containing car information
        """
        soup = BeautifulSoup(html_content, 'lxml')
        cars = []
        
        # Find all vehicle cards
        vehicle_cards = soup.find_all('div', class_='ok-subs-vehicles-card')
        
        for card in vehicle_cards:
            car_data = self._extract_car_data(card)
            if car_data:
                cars.append(car_data)
        
        return cars
    
    def _extract_car_data(self, card) -> Dict[str, Any]:
        """Extract data from a single vehicle card"""
        try:
            # Basic information from data attributes
            car = {
                'sipp_code': card.get('data-sipp', ''),
                'category_id': card.get('data-filter-category', ''),
                'type_id': card.get('data-filter-type', ''),
                'transmission_id': card.get('data-filter-transmission', ''),
                'fuel_id': card.get('data-filter-fuel', ''),
                'seats': int(card.get('data-filter-seat', 0)),
                'min_price': float(card.get('data-min-price', 0)),
                'guaranteed': card.get('data-filter-guaranteed', 'false').lower() == 'true',
            }
            
            # Car name
            name_elem = card.find('h2')
            if name_elem:
                car['name'] = name_elem.get('title', name_elem.text.strip())
            
            # Category/type description (e.g., "or similar | Urban | EMMS")
            info_elem = card.find('span', class_='vehicles-card-info')
            if info_elem:
                info_text = info_elem.get('title', info_elem.text.strip())
                car['description'] = info_text
                # Parse category from description
                parts = [p.strip() for p in info_text.split('|')]
                if len(parts) >= 2:
                    car['category'] = parts[1]
            
            # Equipment details
            equipment = {}
            equipment_items = card.find_all('span', class_='vehicles-card-equipment-item')
            for item in equipment_items:
                text = item.text.strip()
                if 'Seats' in text:
                    equipment['seats'] = text
                elif 'Manual' in text or 'Automatic' in text:
                    equipment['transmission'] = text
                elif 'Doors' in text:
                    equipment['doors'] = text
            car['equipment'] = equipment
            
            # Pricing information
            pricing = {}
            
            # Original price (before discount)
            original_price_elem = card.find('span', class_='vehicles-card-discount-price')
            if original_price_elem:
                price_text = original_price_elem.text.strip()
                pricing['original_price'] = self._extract_price(price_text)
            
            # Discounted price
            new_price_elem = card.find('span', class_='vehicles-card-new-price-quantity')
            if new_price_elem:
                price_text = new_price_elem.text.strip()
                pricing['discounted_price'] = self._extract_price(price_text)
            
            car['pricing'] = pricing
            
            # Duration options
            options_elem = card.find('p', class_='vehicles-card-options')
            if options_elem:
                options_text = options_elem.text.strip()
                # Extract the months part (e.g., "3, 4, 5, 6, 7, 8, 9 months")
                if 'Options:' in options_text:
                    months_text = options_text.split('Options:')[-1].strip()
                    car['duration_options'] = months_text
            
            # Vehicle images
            images = []
            swiper_slides = card.find_all('div', class_='swiper-slide')
            for slide in swiper_slides:
                img = slide.find('img', class_='vehicles-card-img')
                if img and img.get('src'):
                    images.append({
                        'url': img['src'],
                        'alt': img.get('alt', '')
                    })
            car['images'] = images
            
            # Booking URL
            link = card.find('a', class_='ok-subs-vehicles-cards-link')
            if link and link.get('href'):
                car['booking_url'] = link['href']
            
            # Special badges (e.g., Plug-in Hybrid)
            badges = []
            badge_elems = card.find_all('div', class_='vehicle-badge')
            for badge in badge_elems:
                badge_text = badge.text.strip()
                if badge_text:
                    badges.append(badge_text)
            if badges:
                car['badges'] = badges
            
            return car
            
        except Exception as e:
            print(f"Error extracting car data: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text like '414€' or '€414'"""
        # Remove currency symbols and whitespace, extract number
        numbers = re.findall(r'\d+(?:\.\d+)?', price_text)
        if numbers:
            return float(numbers[0])
        return 0.0


def main():
    """Main function to demonstrate scraper usage"""
    scraper = OKMobilityScraper()


    # Optionally scrape from URL (commented out by default)
    print("\nScraping from URL...")
    url = "https://okmobility.com/en/subscription/booking/availability/sevilla-santa-justa-train-station/2026-01-05?onlyGuaranteedModels=false"
    cars = scraper.scrape_from_url(url)
    print(f"Found {len(cars)} cars from URL")

    for i, car in enumerate(cars, 1):
        print(f"{i}. {car['name']} ({car.get('category', 'N/A')})")
        print(f"   SIPP Code: {car['sipp_code']}")
        print(f"   Seats: {car['seats']}")
        print(f"   Equipment: {car.get('equipment', {})}")
        if car.get('pricing'):
            pricing = car['pricing']
            if 'original_price' in pricing and 'discounted_price' in pricing:
                print(f"   Price: €{pricing['discounted_price']}/month (was €{pricing['original_price']})")
            elif 'discounted_price' in pricing:
                print(f"   Price: €{pricing['discounted_price']}/month")
        print(f"   Duration: {car.get('duration_options', 'N/A')}")
        if car.get('badges'):
            print(f"   Badges: {', '.join(car['badges'])}")
        print(f"   Images: {len(car.get('images', []))} available")
        print()
    
    # Save to JSON
    output_file = 'cars_availability.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cars, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to {output_file}")


if __name__ == '__main__':
    main()
