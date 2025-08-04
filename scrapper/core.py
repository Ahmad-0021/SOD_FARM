# scrapper/core.py - NO REVIEWS VERSION with improved coordinate/website extraction
import asyncio
import logging
import platform
import random
import time
from typing import List
from contextlib import asynccontextmanager

from patchright.async_api import async_playwright, Browser, BrowserContext, Page

from .models import Place
from .extractors import extract_place


class BrowserManager:
    """
    A reusable class to manage Patchright browser lifecycle with consistent configuration.
    Adds stealth and human-like behavior.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None

    async def start(self):
        """Launch browser with stealth settings."""
        self.playwright = await async_playwright().start()

        executable_path = (
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if platform.system() == "Windows" else None
        )

        self.browser = await self.playwright.chromium.launch(
            executable_path=executable_path,
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-infobars',
                '--start-maximized',
                '--disable-notifications',
                '--disable-geolocation',
                '--no-first-run',
                '--no-default-browser-check'
            ]
        )

        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768},
            ignore_https_errors=True
        )

        # Stealth: Hide automation flags
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            window.chrome = {
                runtime: {},
                loadTimes: () => {},
                csi: () => {}
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

        return self

    async def new_page(self) -> Page:
        page = await self.context.new_page()
        # Extra stealth: remove Playwright headers
        await page.set_extra_http_headers({"sec-fetch-site": "none"})
        return page

    async def close(self):
        """Safely close browser and Patchright."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    @asynccontextmanager
    async def get_page(self):
        """Context manager for safe page usage."""
        page = await self.new_page()
        try:
            yield page
        except Exception as e:
            logging.error(f"Error in page context: {e}")
            raise
        finally:
            await page.close()


class GoogleMapsScraper:
    """
    Scraper for Google Maps places - NO REVIEWS.
    Focuses on extracting coordinates and website URLs.
    """
    BASE_URL = "https://www.google.com/maps"

    def __init__(self, headless: bool = False):
        self.browser_manager = BrowserManager(headless=headless)

    async def scrape_places(self, search_for: str, total: int) -> List[Place]:
        places: List[Place] = []
        try:
            await self.browser_manager.start()
            async with self.browser_manager.get_page() as page:
                logging.info("🌍 Navigating to Google Maps...")
                await page.goto(self.BASE_URL, timeout=60000)
                await asyncio.sleep(random.uniform(2.0, 4.0))

                # Search query
                logging.info(f"🔍 Searching for: {search_for}")
                search_box = page.locator('//input[@id="searchboxinput"]')
                await search_box.fill(search_for)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2.5)

                # Wait for results
                try:
                    await page.wait_for_selector('//a[contains(@href, "/maps/place/")]', timeout=20000)
                    logging.info("✅ Search results loaded")
                except Exception:
                    logging.error("❌ No results found or timeout")
                    return places

                # IMPROVED SCROLLING LOGIC
                listings_locator = page.locator('//a[contains(@href, "/maps/place/")]')
                previously_counted = 0
                scroll_attempts = 0
                max_scroll_attempts = 30
                no_new_results_count = 0

                logging.info(f"🎯 Target: {total} places")
                
                while scroll_attempts < max_scroll_attempts:
                    await page.mouse.wheel(0, 15000)
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    
                    found = await listings_locator.count()
                    logging.info(f"📌 Found {found} places (attempt {scroll_attempts + 1})")

                    if found >= total:
                        logging.info(f"🎉 Reached target of {total} places!")
                        break
                        
                    if found == previously_counted:
                        no_new_results_count += 1
                        logging.info(f"⏳ No new results ({no_new_results_count}/5)")
                        
                        if no_new_results_count == 2:
                            try:
                                sidebar = page.locator('[role="main"]')
                                if await sidebar.count() > 0:
                                    await sidebar.scroll_into_view_if_needed()
                                    await page.mouse.wheel(0, 10000)
                                    logging.info("🔄 Tried scrolling sidebar")
                            except:
                                pass
                                
                        if no_new_results_count >= 5:
                            logging.info("🛑 No more new places loading after 5 attempts.")
                            break
                    else:
                        no_new_results_count = 0
                        
                    previously_counted = found
                    scroll_attempts += 1

                # Get listings
                buffer_multiplier = 1.5
                target_raw_listings = min(int(total * buffer_multiplier), await listings_locator.count())
                raw_listings = await listings_locator.all()
                listings = [listing.locator("xpath=..") for listing in raw_listings[:target_raw_listings]]
                
                logging.info(f"📬 Processing {len(listings)} place listings (targeting {total} valid places)...")

                # Process each place
                for idx, listing in enumerate(listings):
                    if len(places) >= total:
                        logging.info(f"🎯 Reached target of {total} valid places!")
                        break
                        
                    try:
                        logging.info(f"📍 Processing place {idx + 1}/{len(listings)} (valid: {len(places)}/{total})")

                        # Human-like delay before interaction
                        await asyncio.sleep(random.uniform(1.5, 3.5))

                        # Click listing with retry logic
                        max_click_attempts = 3
                        click_success = False
                        
                        for click_attempt in range(max_click_attempts):
                            try:
                                await listing.click(timeout=5000)
                                click_success = True
                                break
                            except Exception as e:
                                logging.warning(f"⚠️ Click attempt {click_attempt + 1} failed: {str(e)}")
                                if click_attempt < max_click_attempts - 1:
                                    await asyncio.sleep(1)
                                    
                        if not click_success:
                            logging.error(f"❌ Failed to click listing {idx + 1} after {max_click_attempts} attempts")
                            continue

                        logging.info("⏳ Waiting for place details to load...")
                        await page.wait_for_timeout(4000)
                        await page.wait_for_timeout(random.randint(1000, 2000))

                        # EXTRACT COORDINATES FROM URL FIRST (most reliable method)
                        current_url = page.url
                        coordinates = await self.extract_coordinates_from_url(current_url)
                        
                        # Extract basic place data
                        place = await extract_place(page)
                        
                        # Override coordinates if we got them from URL
                        if coordinates:
                            place.latitude = coordinates['latitude']
                            place.longitude = coordinates['longitude']
                            logging.info(f"🗺️ Coordinates from URL: {place.latitude}, {place.longitude}")
                        
                        # Try additional coordinate extraction if still missing
                        if not place.has_coordinates():
                            logging.info("🔍 Trying additional coordinate extraction methods...")
                            additional_coords = await self.extract_coordinates_advanced(page)
                            if additional_coords:
                                place.latitude = additional_coords['latitude']
                                place.longitude = additional_coords['longitude']
                                logging.info(f"🗺️ Coordinates from advanced: {place.latitude}, {place.longitude}")
                        
                        # Try additional website extraction if missing
                        if not place.website:
                            logging.info("🔍 Trying additional website extraction methods...")
                            website = await self.extract_website_advanced(page)
                            if website:
                                place.website = website
                                logging.info(f"🌐 Website found: {place.website}")

                        # Try additional image extraction if missing
                        if not place.image_url:
                            logging.info("🔍 Trying additional image extraction methods...")
                            image_url = await self.extract_image_advanced(page)
                            if image_url:
                                place.image_url = image_url
                                logging.info(f"🖼️ Image found: {place.image_url}")

                        if not place.name or place.name in ["", "Unknown", "Failed to extract"]:
                            logging.warning(f"⚠️ Skipping place {idx + 1} - invalid name: {place.name}")
                            continue

                        places.append(place)

                        # Log success with all fields
                        logging.info(
                            f"✅ Added ({len(places)}/{total}): {place.name} | "
                            f"⭐ {place.rating or 'N/A'} ({place.reviews_count or 0} reviews) | "
                            f"📞 {place.phone or 'No phone'} | "
                            f"🌐 {place.website or 'No website'} | "
                            f"🖼️ {place.image_url or 'No image'} | "
                            f"📍 {f'({place.latitude}, {place.longitude})' if place.has_coordinates() else 'No coordinates'}"
                        )

                        # Human-like pause after reading a place
                        wait_time = random.uniform(2.5, 6.0)
                        logging.info(f"⏸️  Sleeping for {wait_time:.2f}s before next place...")
                        await asyncio.sleep(wait_time)

                    except Exception as e:
                        logging.error(f"❌ Failed processing listing {idx + 1}: {str(e)}")
                        await asyncio.sleep(random.uniform(1.0, 3.0))
                        continue

        except Exception as e:
            logging.error(f"🚨 Scraping error: {str(e)}")
        finally:
            await self.browser_manager.close()

        logging.info(f"🎉 Scraping completed! Extracted {len(places)} places (requested: {total}).")
        return places

    async def extract_coordinates_from_url(self, url: str) -> dict or None:
        """Extract coordinates from Google Maps URL - most reliable method."""
        import re
        try:
            # Pattern for coordinates in URL: /@lat,lng,zoom
            coord_match = re.search(r'/@(-?\d+\.?\d*),(-?\d+\.?\d*),', url)
            if coord_match:
                latitude = float(coord_match.group(1))
                longitude = float(coord_match.group(2))
                # Validate coordinates
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    return {'latitude': latitude, 'longitude': longitude}
        except Exception as e:
            logging.debug(f"Failed to extract coordinates from URL: {e}")
        return None

    async def extract_coordinates_advanced(self, page: Page) -> dict or None:
        """Advanced coordinate extraction from page content."""
        import re
        try:
            # Get page content
            page_content = await page.content()
            
            # Multiple regex patterns for finding coordinates
            patterns = [
                r'null,\[null,null,(-?\d+\.?\d*),(-?\d+\.?\d*)\]',
                r'\[(-?\d+\.?\d*),(-?\d+\.?\d*)\]',
                r'"lat":(-?\d+\.?\d*),"lng":(-?\d+\.?\d*)',
                r'latitude.*?(-?\d+\.?\d*).*?longitude.*?(-?\d+\.?\d*)',
                r'center.*?\[(-?\d+\.?\d*),(-?\d+\.?\d*)\]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    try:
                        for match in matches:
                            lat, lng = match[0], match[1]
                            latitude = float(lat)
                            longitude = float(lng)
                            # Validate coordinates
                            if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                                return {'latitude': latitude, 'longitude': longitude}
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            logging.debug(f"Advanced coordinate extraction failed: {e}")
        return None

    async def extract_website_advanced(self, page: Page) -> str or None:
        """Advanced website extraction with multiple strategies."""
        try:
            # Strategy 1: Look for website buttons/links
            selectors = [
                'a[data-item-id="authority"]',
                'a[aria-label*="Website"]',
                'a[data-value="Website"]',
                'button[data-item-id="authority"]',
                '[data-item-id="authority"] a',
                'a[href*="http"]:has-text("Website")',
                'a[jsaction*="website"]',
                '.rogA2c a[href^="http"]'  # New selector for website links
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        href = await element.get_attribute('href')
                        if href and href.startswith('http'):
                            # Clean up Google redirect URLs
                            if 'google.com/url?q=' in href:
                                import urllib.parse
                                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                                if 'q' in parsed:
                                    return parsed['q'][0]
                            return href
                except Exception:
                    continue
            
            # Strategy 2: Try clicking on contact/info buttons to reveal website
            info_buttons = [
                'button:has-text("Website")',
                '[aria-label*="website" i]',
                'button[data-value*="website" i]'
            ]
            
            for selector in info_buttons:
                try:
                    button = page.locator(selector).first
                    if await button.count() > 0:
                        await button.click(timeout=3000)
                        await page.wait_for_timeout(1000)
                        
                        # Look for revealed website link
                        link = page.locator('a[href^="http"]').first
                        if await link.count() > 0:
                            href = await link.get_attribute('href')
                            if href:
                                return href
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logging.debug(f"Advanced website extraction failed: {e}")
        return None


    async def extract_image_advanced(self, page: Page) -> str or None:
        """Advanced image extraction with multiple strategies."""
        try:
            # Strategy 1: Look for main business image/photo
            selectors = [
                'img[data-src*="googleusercontent.com"]',  # Google's CDN images
                'img[src*="googleusercontent.com"]',
                'button img[src*="googleusercontent.com"]',  # Images in buttons
                '.ZKCDEc img',  # Main image container
                '.UCw5gc img',  # Another image container
                '[data-photo-index="0"] img',  # First photo
                'img[alt*="Photo"]',  # Images with photo alt text
                '.gallery img',  # Gallery images
                'img[src*="streetviewpixels"]',  # Street view images
                'img[src*="places"]',  # Places images
                '[jsaction*="photo"] img'  # Interactive photo elements
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
                        
                        if img_url and self.is_valid_image_url(img_url):
                            # Clean up the image URL
                            cleaned_url = self.clean_image_url(img_url)
                            if cleaned_url:
                                logging.info(f"✅ Image found with selector '{selector}': {cleaned_url}")
                                return cleaned_url
                except Exception:
                    continue
            
            # Strategy 2: Look for images in photo galleries or carousels
            try:
                gallery_selectors = [
                    '.section-image img',
                    '.photo-container img',
                    '[data-value*="photo"] img',
                    '.RZ66Rb img'  # Photo gallery
                ]
                
                for selector in gallery_selectors:
                    elements = page.locator(selector)
                    count = await elements.count()
                    if count > 0:
                        # Get the first image
                        first_img = elements.first
                        img_url = await first_img.get_attribute('data-src') or await first_img.get_attribute('src')
                        if img_url and self.is_valid_image_url(img_url):
                            cleaned_url = self.clean_image_url(img_url)
                            if cleaned_url:
                                logging.info(f"✅ Gallery image found: {cleaned_url}")
                                return cleaned_url
                        
            except Exception:
                pass
            
            # Strategy 3: Try clicking on photo buttons to reveal images
            try:
                photo_buttons = [
                    'button:has-text("Photo")',
                    '[aria-label*="photo" i]',
                    'button[data-value*="photo" i]',
                    '[jsaction*="photo"]'
                ]
                
                for selector in photo_buttons:
                    button = page.locator(selector).first
                    if await button.count() > 0:
                        await button.click(timeout=3000)
                        await page.wait_for_timeout(1000)
                        
                        # Look for revealed images
                        revealed_img = page.locator('img[src*="googleusercontent.com"]').first
                        if await revealed_img.count() > 0:
                            img_url = await revealed_img.get_attribute('src')
                            if img_url and self.is_valid_image_url(img_url):
                                cleaned_url = self.clean_image_url(img_url)
                                if cleaned_url:
                                    logging.info(f"✅ Image found after clicking: {cleaned_url}")
                                    return cleaned_url
                        break
                        
            except Exception:
                pass
                    
        except Exception as e:
            logging.debug(f"Advanced image extraction failed: {e}")
        return None

    def is_valid_image_url(self, url: str) -> bool:
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
        
        return any(indicator in url.lower() for indicator in valid_indicators)

    def clean_image_url(self, url: str) -> str or None:
        """Clean and optimize image URL."""
        try:
            if not url:
                return None
            
            # Handle protocol-relative URLs
            if url.startswith('//'):
                url = 'https:' + url
            
            # Remove unnecessary parameters for better image quality
            if 'googleusercontent.com' in url:
                # Remove size restrictions to get full-size image
                import re
                # Remove size parameters like =s100-k-no or =w100-h100
                url = re.sub(r'=s\d+-.*?(?=&|$)', '', url)
                url = re.sub(r'=w\d+-h\d+.*?(?=&|$)', '', url)
                # Add high quality parameters
                if '=' not in url:
                    url += '=s1000'  # Request up to 1000px size
                else:
                    url += '&s=1000'
            
            return url
            
        except Exception as e:
            logging.debug(f"Failed to clean image URL {url}: {e}")
            return url  # Return original if cleaning fails


# PUBLIC FUNCTIONS
def scrape_places(search_for: str, total: int) -> List[Place]:
    """
    Public synchronous interface for scraping Google Maps places.
    NO REVIEWS - focuses on coordinates and website extraction.
    """
    logging.info(f"🚀 Starting scraping for '{search_for}' - Target: {total} places")
    return asyncio.run(_scrape_places_async(search_for, total))


async def _scrape_places_async(search_for: str, total: int) -> List[Place]:
    """Internal async implementation."""
    scraper = GoogleMapsScraper(headless=False)
    return await scraper.scrape_places(search_for, total)


def scrape_places_headless(search_for: str, total: int) -> List[Place]:
    """Headless version."""
    logging.info(f"🚀 Starting headless scraping for '{search_for}' - Target: {total} places")
    return asyncio.run(_scrape_places_headless_async(search_for, total))


async def _scrape_places_headless_async(search_for: str, total: int) -> List[Place]:
    """Internal headless async implementation."""
    scraper = GoogleMapsScraper(headless=True)
    return await scraper.scrape_places(search_for, total)


__all__ = ['scrape_places', 'scrape_places_headless', 'GoogleMapsScraper', 'BrowserManager']