# main.py - Example usage without reviews

import logging
from scrapper.core import scrape_places
from scrapper.utils import save_places_to_csv, print_places_summary, export_places_json, setup_logging


def main():
    """Main function to demonstrate scraping without reviews."""
    
    # Setup logging
    setup_logging("INFO")  # Change to "DEBUG" for more detailed logs
    
    # Configuration
    search_query = "sod farms in usa"  # Change this to your search
    total_places = 10  # Number of places to scrape
    
    print(f"🚀 Starting Google Maps Scraping")
    print(f"Search: {search_query}")
    print(f"Target: {total_places} places")
    print(f"Features: Name, Address, Phone, Website, Image, Rating, Coordinates")
    print("=" * 60)
    
    try:
        # Scrape places
        places = scrape_places(search_query, total_places)
        
        if places:
            # Print summary
            print_places_summary(places)
            
            # Save to CSV
            csv_filename = f"places_{search_query.replace(' ', '_').replace(',', '')}.csv"
            save_places_to_csv(places, csv_filename)
            
            # Save to JSON (optional)
            json_filename = f"places_{search_query.replace(' ', '_').replace(',', '')}.json"
            export_places_json(places, json_filename)
            
            # Print detailed results
            print("📋 DETAILED RESULTS:")
            print("-" * 60)
            for i, place in enumerate(places, 1):
                print(f"{i}. {place.name}")
                print(f"   Address: {place.address or 'N/A'}")
                print(f"   Phone: {place.phone or 'N/A'}")
                print(f"   Website: {place.website or 'N/A'}")
                print(f"   Image: {place.image_url or 'N/A'}")
                print(f"   Rating: {place.rating or 'N/A'} ({place.reviews_count or 0} reviews)")
                print(f"   Coordinates: {f'({place.latitude}, {place.longitude})' if place.has_coordinates() else 'N/A'}")
                if place.has_coordinates():
                    print(f"   Google Maps: {place.get_google_maps_url()}")
                print()
            
            print(f"✅ Scraping completed successfully!")
            print(f"📁 Files saved in 'output' directory")
            
        else:
            print("❌ No places were scraped. Check your search query and try again.")
            
    except Exception as e:
        logging.error(f"🚨 Scraping failed: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()