# extractors.py - NO REVIEWS VERSION with improved coordinate/website extraction

import asyncio
import logging
import re
from typing import Optional
from patchright.async_api import Page
from .models import Place


async def extract_place(page: Page) -> Place:
    """
    Extract place information WITHOUT reviews.
    Focus on getting accurate coordinates and website URL.
    """
    place = Place()
    
    try:
        # Extract basic information
        place.name = await extract_name(page)
        place.address = await extract_address(page)
        place.phone = await extract_phone(page)
        place.rating = await extract_rating(page)
        place.reviews_count = await extract_reviews_count(page)
        
        # Extract website URL with improved logic
        place.website = await extract_website(page)
        
        # Extract image URL with improved logic
        place.image_url = await extract_image(page)
        
        # Extract coordinates with improved logic
        coordinates = await extract_coordinates(page)
        if coordinates:
            place.latitude = coordinates.get('latitude')
            place.longitude = coordinates.get('longitude')
        
        logging.info(f"Extracted: {place.name} | Website: {place.website} | Image: {place.image_url} | Coords: ({place.latitude}, {place.longitude})")
        
    except Exception as e:
        logging.error(f"Error extracting place data: {e}")
    
    return place


async def extract_name(page: Page) -> Optional[str]:
    """Extract place name with improved selectors."""
    selectors = [
        'h1[data-attrid="title"]',
        'h1.DUwDvf',
        '[data-attrid="title"] h1',
        'h1.x3AX1-LfntMc-header-title-title',
        '.x3AX1-LfntMc-header-title h1',
        'h1',
        '.qrShPb h1',
        '.SPZz6b h1'
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                name = await element.text_content()
                if name and name.strip() and len(name.strip()) > 0:
                    return name.strip()
        except:
            continue
    
    return "Unknown"


async def extract_address(page: Page) -> Optional[str]:
    """Extract place address with improved selectors."""
    selectors = [
        '[data-item-id="address"] .Io6YTe',
        '.Io6YTe[data-value="Address"]',
        'button[data-item-id="address"]',
        '[data-attrid="kc:/location/location:address"]',
        '.rogA2c .Io6YTe',
        '[data-item-id="address"] span',
        'button[data-item-id="address"] .Io6YTe'
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                address = await element.text_content()
                if address and address.strip():
                    return address.strip()
        except:
            continue
    
    return None


async def extract_phone(page: Page) -> Optional[str]:
    """Extract phone number with improved selectors."""
    selectors = [
        '[data-item-id="phone:tel:"] .Io6YTe',
        'button[data-item-id^="phone"]',
        '[data-value*="phone"] .Io6YTe',
        'a[href^="tel:"]',
        '[data-item-id*="phone"] span',
        '.rogA2c a[href^="tel:"]'
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                phone = await element.text_content()
                if phone and phone.strip():
                    return phone.strip()
        except:
            continue
    
    return None


async def extract_rating(page: Page) -> Optional[float]:
    """Extract rating with improved selectors."""
    selectors = [
        '.MW4etd',
        '.ceNzKf',
        '[jsaction*="pane.rating"]',
        '.fontDisplayLarge',
        'span.ceNzKf[aria-hidden="true"]'
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                rating_text = await element.text_content()
                if rating_text:
                    # Extract number from rating text
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text.strip())
                    if rating_match:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:  # Validate rating range
                            return rating
        except:
            continue
    
    return None


async def extract_reviews_count(page: Page) -> Optional[int]:
    """Extract number of reviews with improved selectors."""
    selectors = [
        '.UY7F9',
        'button[aria-label*="reviews"]',
        '[data-value="Reviews count"]',
        '.fontTitleSmall .UY7F9',
        'span.UY7F9'
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                reviews_text = await element.text_content()
                if reviews_text:
                    # Extract number from reviews text (e.g., "(123)" or "123 reviews")
                    reviews_match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                    if reviews_match:
                        return int(reviews_match.group(1))
        except:
            continue
    
    return None


async def extract_coordinates(page: Page) -> Optional[dict]:
    """
    IMPROVED coordinate extraction with multiple fallback methods.
    """
    coordinates = None
    
    # Method 1: Extract from URL (most reliable)
    try:
        current_url = page.url
        logging.info(f"🗺️ Extracting coordinates from URL: {current_url}")
        
        # Multiple URL patterns for coordinates
        patterns = [
            r'/@(-?\d+\.?\d*),(-?\d+\.?\d*),',  # Standard pattern
            r'/place/[^/]+/@(-?\d+\.?\d*),(-?\d+\.?\d*)',  # Place-specific
            r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)',  # Alternative format
            r'center=(-?\d+\.?\d*),(-?\d+\.?\d*)',  # Center parameter
        ]
        
        for pattern in patterns:
            coord_match = re.search(pattern, current_url)
            if coord_match:
                latitude = float(coord_match.group(1))
                longitude = float(coord_match.group(2))
                # Validate coordinates
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    coordinates = {'latitude': latitude, 'longitude': longitude}
                    logging.info(f"✅ Coordinates from URL: {latitude}, {longitude}")
                    return coordinates
                    
    except Exception as e:
        logging.debug(f"Failed to extract coordinates from URL: {e}")
    
    # Method 2: Extract from page content/scripts
    try:
        await page.wait_for_timeout(1000)  # Wait for scripts to load
        page_content = await page.content()
        
        # Enhanced patterns for finding coordinates in page content
        coord_patterns = [
            r'null,\[null,null,(-?\d+\.?\d*),(-?\d+\.?\d*)\]',
            r'\[(-?\d+\.?\d*),(-?\d+\.?\d*)\]',
            r'"lat":(-?\d+\.?\d*),"lng":(-?\d+\.?\d*)',
            r'"latitude":(-?\d+\.?\d*),"longitude":(-?\d+\.?\d*)',
            r'center.*?\[(-?\d+\.?\d*),(-?\d+\.?\d*)\]',
            r'position.*?(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'coordinates.*?\[(-?\d+\.?\d*),(-?\d+\.?\d*)\]'
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, page_content)
            if matches:
                try:
                    # Try all matches, sometimes first match is not the right one
                    for match in matches:
                        lat, lng = match[0], match[1]
                        latitude = float(lat)
                        longitude = float(lng)
                        # Validate coordinates and check if they seem reasonable
                        if (-90 <= latitude <= 90 and -180 <= longitude <= 180 and 
                            abs(latitude) > 0.001 and abs(longitude) > 0.001):  # Not (0,0)
                            coordinates = {'latitude': latitude, 'longitude': longitude}
                            logging.info(f"✅ Coordinates from content: {latitude}, {longitude}")
                            return coordinates
                except (ValueError, IndexError):
                    continue
                    
    except Exception as e:
        logging.debug(f"Failed to extract coordinates from page content: {e}")
    
    # Method 3: Try to extract from data attributes
    try:
        data_selectors = [
            '[data-lat][data-lng]',
            '[data-latitude][data-longitude]',
            '[data-coords]',
            '[jsaction*="coordinates"]'
        ]
        
        for selector in data_selectors:
            element = page.locator(selector).first
            if await element.count() > 0:
                lat = (await element.get_attribute('data-lat') or 
                      await element.get_attribute('data-latitude'))
                lng = (await element.get_attribute('data-lng') or 
                      await element.get_attribute('data-longitude'))
                
                if lat and lng:
                    latitude = float(lat)
                    longitude = float(lng)
                    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                        coordinates = {'latitude': latitude, 'longitude': longitude}
                        logging.info(f"✅ Coordinates from attributes: {latitude}, {longitude}")
                        return coordinates
                        
    except Exception as e:
        logging.debug(f"Failed to extract coordinates from attributes: {e}")
    
    if not coordinates:
        logging.warning("⚠️ Could not extract coordinates from any method")
    
    return coordinates


async def extract_website(page: Page) -> Optional[str]:
    """
    IMPROVED website URL extraction with multiple strategies and better cleaning.
    """
    # Strategy 1: Direct selectors for website links
    selectors = [
        'a[data-item-id="authority"]',  # Primary website button
        'a[aria-label*="Website" i]',   # Case insensitive
        'a[data-value="Website"]',
        'button[data-item-id="authority"] a',
        '[data-item-id="authority"] a[href]',
        'a[href*="http"]:has-text("Website")',
        'a[jsaction*="website"]',
        '.rogA2c a[href^="http"]',  # Website in contact section
        'a[data-item-id="authority"] .Io6YTe',
        '.CsEnBe a[href^="http"]'  # Another potential container
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                href = await element.get_attribute('href')
                if href and href.startswith('http'):
                    # Clean up the URL
                    cleaned_url = await clean_website_url(href)
                    if cleaned_url:
                        logging.info(f"✅ Website found with selector '{selector}': {cleaned_url}")
                        return cleaned_url
                
                # If no href, try getting text content that might be a URL
                text_content = await element.text_content()
                if text_content and ('http' in text_content or 'www.' in text_content):
                    url = text_content.strip()
                    if not url.startswith('http'):
                        url = 'https://' + url.lstrip('www.')
                    cleaned_url = await clean_website_url(url)
                    if cleaned_url:
                        logging.info(f"✅ Website from text: {cleaned_url}")
                        return cleaned_url
                        
        except Exception as e:
            logging.debug(f"Failed with selector {selector}: {e}")
            continue
    
    # Strategy 2: Look for website in expanded contact info
    try:
        # Try to find and click contact/info buttons that might reveal website
        info_buttons = [
            'button:has-text("Website")',
            '[aria-label*="website" i]',
            'button[data-value*="website" i]',
            'button:has-text("Visit website")',
            '.RcCsl button'  # Contact info buttons
        ]
        
        for selector in info_buttons:
            try:
                button = page.locator(selector).first
                if await button.count() > 0:
                    # Try clicking to reveal website
                    await button.click(timeout=3000)
                    await page.wait_for_timeout(1000)
                    
                    # Look for revealed website link
                    revealed_link = page.locator('a[href^="http"]').first
                    if await revealed_link.count() > 0:
                        href = await revealed_link.get_attribute('href')
                        if href:
                            cleaned_url = await clean_website_url(href)
                            if cleaned_url:
                                logging.info(f"✅ Website found after clicking: {cleaned_url}")
                                return cleaned_url
                    break
            except Exception:
                continue
                
    except Exception as e:
        logging.debug(f"Failed to extract website through clicking: {e}")
    
    # Strategy 3: Search in page content for website URLs
    try:
        page_content = await page.content()
        
        # Look for website URLs in the page content
        url_patterns = [
            r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s"\'<>]*)?',
            r'www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s"\'<>]*)?'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                if not any(exclude in match.lower() for exclude in 
                          ['google.com', 'gstatic.com', 'googleapis.com', 'youtube.com', 'facebook.com']):
                    if not match.startswith('http'):
                        match = 'https://' + match
                    cleaned_url = await clean_website_url(match)
                    if cleaned_url:
                        logging.info(f"✅ Website from content: {cleaned_url}")
                        return cleaned_url
                        
    except Exception as e:
        logging.debug(f"Failed to extract website from content: {e}")
    
    logging.debug("❌ No website URL found")
    return None


async def extract_image(page: Page) -> Optional[str]:
    """
    Extract main business image URL from Google Maps place page.
    """
    # Primary selectors for business images
    selectors = [
        'img[data-src*="googleusercontent.com"]',  # Main Google CDN images
        'img[src*="googleusercontent.com"]',
        'button img[src*="googleusercontent.com"]',  # Images in buttons
        '.ZKCDEc img',  # Main image container
        '.UCw5gc img',  # Another image container
        '[data-photo-index="0"] img',  # First photo in gallery
        'img[alt*="Photo"]',  # Images with photo alt text
        '.gallery img:first-child',  # First gallery image
        'img[src*="streetviewpixels"]',  # Street view images
        'img[src*="places"]',  # Google Places images
        '[jsaction*="photo"] img:first-child'  # First interactive photo
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                # Try data-src first (lazy loaded images)
                img_url = await element.get_attribute('data-src')
                if not img_url:
                    # Fallback to src attribute
                    img_url = await element.get_attribute('src')
                
                if img_url and is_valid_image_url(img_url):
                    # Clean up the image URL
                    cleaned_url = clean_image_url(img_url)
                    if cleaned_url:
                        logging.info(f"✅ Image URL extracted: {cleaned_url}")
                        return cleaned_url
        except Exception:
            continue
    
    # Fallback: Try to find any reasonable image
    try:
        fallback_selectors = [
            'img[src*="http"]',
            'img[data-src*="http"]'
        ]
        
        for selector in fallback_selectors:
            elements = page.locator(selector)
            count = await elements.count()
            
            for i in range(min(count, 5)):  # Check first 5 images
                element = elements.nth(i)
                img_url = await element.get_attribute('data-src') or await element.get_attribute('src')
                
                if img_url and is_valid_image_url(img_url):
                    cleaned_url = clean_image_url(img_url)
                    if cleaned_url:
                        logging.info(f"✅ Fallback image URL extracted: {cleaned_url}")
                        return cleaned_url
                        
    except Exception:
        pass
    
    logging.debug("❌ No image URL found")
    return None


def is_valid_image_url(url: str) -> bool:
    """Check if URL is a valid image URL."""
    if not url or not isinstance(url, str):
        return False
    
    # Check if it's a proper URL
    if not url.startswith(('http://', 'https://', '//')):
        return False
    
    # Check if it contains image-related domains or paths
    valid_indicators = [
        'googleusercontent.com',
        'streetviewpixels',
        'places',
        'maps.gstatic.com',
        '.jpg', '.jpeg', '.png', '.webp'
    ]
    
    # Exclude obviously wrong URLs
    invalid_indicators = [
        'data:image',  # Base64 images
        'blob:',       # Blob URLs
        'avatar',      # User avatars
        'profile'      # Profile pictures
    ]
    
    url_lower = url.lower()
    
    # Must have valid indicators and not have invalid ones
    has_valid = any(indicator in url_lower for indicator in valid_indicators)
    has_invalid = any(indicator in url_lower for indicator in invalid_indicators)
    
    return has_valid and not has_invalid


def clean_image_url(url: str) -> Optional[str]:
    """Clean and optimize image URL for better quality."""
    try:
        if not url:
            return None
        
        # Handle protocol-relative URLs
        if url.startswith('//'):
            url = 'https:' + url
        
        # Optimize Google User Content URLs for better quality
        if 'googleusercontent.com' in url:
            import re
            # Remove size restrictions to get larger image
            url = re.sub(r'=s\d+-.*?(?=&|$)', '', url)
            url = re.sub(r'=w\d+-h\d+.*?(?=&|$)', '', url)
            
            # Add high quality parameters
            if '=' not in url:
                url += '=s800'  # Request up to 800px size
            elif not re.search(r'=s\d+', url):
                url += '&s=800'
        
        return url
        
    except Exception as e:
        logging.debug(f"Failed to clean image URL {url}: {e}")
        return url  # Return original if cleaning fails


async def clean_website_url(url: str) -> Optional[str]:
    """
    Clean and validate website URL.
    Removes Google redirects and validates the URL.
    """
    try:
        import urllib.parse
        
        # Handle Google redirect URLs
        if 'google.com/url?q=' in url:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if 'q' in parsed and parsed['q']:
                url = parsed['q'][0]
        
        # Clean up the URL
        url = url.strip()
        
        # Add protocol if missing
        if url.startswith('www.'):
            url = 'https://' + url
        elif not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic validation
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.netloc and '.' in parsed_url.netloc:
            # Filter out obviously wrong URLs
            excluded_domains = [
                'google.com', 'gstatic.com', 'googleapis.com', 
                'maps.google.com', 'youtube.com', 'facebook.com/tr'
            ]
            
            if not any(domain in parsed_url.netloc.lower() for domain in excluded_domains):
                return url
                
    except Exception as e:
        logging.debug(f"Failed to clean URL {url}: {e}")
    
    return None