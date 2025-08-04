# utils.py - NO REVIEWS VERSION - utility functions for places

import csv
import logging
import os
from typing import List
from .models import Place


def save_places_to_csv(places: List[Place], filename: str = "places.csv") -> None:
    """
    Save places to CSV file without reviews.
    
    Args:
        places: List of Place objects
        filename: Output CSV filename
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow(Place.csv_headers())
            
            # Write place data
            for place in places:
                writer.writerow(place.to_csv_row())
        
        logging.info(f"💾 Saved {len(places)} places to {filepath}")
        
    except Exception as e:
        logging.error(f"❌ Failed to save places to CSV: {e}")


def print_places_summary(places: List[Place]) -> None:
    """
    Print a summary of scraped places.
    
    Args:
        places: List of Place objects
    """
    print(f"\n{'='*60}")
    print(f"📊 SCRAPING SUMMARY")
    print(f"{'='*60}")
    print(f"Total places scraped: {len(places)}")
    
    # Count places with different data
    with_phone = sum(1 for p in places if p.phone)
    with_website = sum(1 for p in places if p.website)
    with_image = sum(1 for p in places if p.image_url)
    with_coordinates = sum(1 for p in places if p.has_coordinates())
    with_rating = sum(1 for p in places if p.rating)
    
    print(f"Places with phone: {with_phone}/{len(places)} ({with_phone/len(places)*100:.1f}%)")
    print(f"Places with website: {with_website}/{len(places)} ({with_website/len(places)*100:.1f}%)")
    print(f"Places with image: {with_image}/{len(places)} ({with_image/len(places)*100:.1f}%)")
    print(f"Places with coordinates: {with_coordinates}/{len(places)} ({with_coordinates/len(places)*100:.1f}%)")
    print(f"Places with rating: {with_rating}/{len(places)} ({with_rating/len(places)*100:.1f}%)")
    
    # Show sample places
    print(f"\n📍 SAMPLE PLACES:")
    print(f"{'-'*60}")
    for i, place in enumerate(places[:3]):  # Show first 3 places
        print(f"{i+1}. {place.name}")
        print(f"   📍 {place.address or 'No address'}")
        print(f"   📞 {place.phone or 'No phone'}")
        print(f"   🌐 {place.website or 'No website'}")
        print(f"   🖼️ {place.image_url or 'No image'}")
        print(f"   ⭐ {place.rating or 'No rating'} ({place.reviews_count or 0} reviews)")
        print(f"   🗺️  {f'({place.latitude}, {place.longitude})' if place.has_coordinates() else 'No coordinates'}")
        print()
    
    if len(places) > 3:
        print(f"   ... and {len(places) - 3} more places")
    
    print(f"{'='*60}\n")


def validate_place_data(place: Place) -> dict:
    """
    Validate place data and return validation results.
    
    Args:
        place: Place object to validate
        
    Returns:
        dict: Validation results
    """
    validation = {
        'valid': True,
        'issues': []
    }
    
    # Check required fields
    if not place.name or place.name.strip() == "":
        validation['valid'] = False
        validation['issues'].append("Missing or empty name")
    
    # Check coordinates if present
    if place.latitude is not None or place.longitude is not None:
        if not place.has_coordinates():
            validation['valid'] = False
            validation['issues'].append("Invalid coordinates")
    
    # Check rating if present
    if place.rating is not None:
        if not (0 <= place.rating <= 5):
            validation['valid'] = False
            validation['issues'].append("Invalid rating (must be 0-5)")
    
    # Check website URL format if present
    if place.website:
        if not place.website.startswith(('http://', 'https://')):
            validation['issues'].append("Website URL missing protocol")
    
    return validation


def filter_valid_places(places: List[Place]) -> List[Place]:
    """
    Filter out places with invalid data.
    
    Args:
        places: List of Place objects
        
    Returns:
        List[Place]: Filtered list of valid places
    """
    valid_places = []
    
    for place in places:
        validation = validate_place_data(place)
        if validation['valid']:
            valid_places.append(place)
        else:
            logging.warning(f"⚠️ Filtered out invalid place: {place.name} - Issues: {validation['issues']}")
    
    logging.info(f"✅ Filtered places: {len(valid_places)}/{len(places)} valid")
    return valid_places


def export_places_json(places: List[Place], filename: str = "places.json") -> None:
    """
    Export places to JSON file.
    
    Args:
        places: List of Place objects
        filename: Output JSON filename
    """
    try:
        import json
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        
        # Convert places to dictionaries
        places_data = [place.to_dict() for place in places]
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(places_data, jsonfile, indent=2, ensure_ascii=False)
        
        logging.info(f"💾 Exported {len(places)} places to {filepath}")
        
    except Exception as e:
        logging.error(f"❌ Failed to export places to JSON: {e}")


def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )