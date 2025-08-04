# reviews.py - SIMPLE PATCHRIGHT VERSION
import asyncio
import logging
import re
from typing import List, Dict
from patchright.async_api import Page

# Simple review dictionary instead of complex model
async def extract_reviews(page: Page) -> List[Dict]:
    """Extract reviews from Google Maps place page"""
    reviews = []
    
    try:
        logging.info("Scrolling to load reviews...")
        
        # Try to find and click reviews tab/button
        try:
            # Multiple selectors for reviews tab
            reviews_selectors = [
                '//button[contains(@data-value, "Sort")]',
                '//button[contains(@aria-label, "reviews") or contains(@aria-label, "Reviews")]',
                '//div[contains(@role, "tablist")]//button[contains(text(), "Reviews")]',
                '//button[contains(@jsaction, "pane.reviewChart")]',
                '//button[@data-tab-index="1"]'  # Often the reviews tab
            ]
            
            for selector in reviews_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        await button.first.click()
                        logging.info("Clicked reviews tab")
                        await asyncio.sleep(3)
                        break
                except:
                    continue
        except Exception as e:
            logging.debug(f"Failed to click reviews tab: {e}")
        
        # Wait a bit for reviews to load
        await asyncio.sleep(3)
        
        # Try to scroll to reviews section
        try:
            reviews_section = page.locator('//div[contains(@aria-label, "Reviews") or contains(@class, "review")]')
            if await reviews_section.count() > 0:
                await reviews_section.first.scroll_into_view_if_needed()
                await asyncio.sleep(1)
        except:
            pass
        
        # Multiple selectors for review elements (Google Maps changes these frequently)
        review_selectors = [
            '//div[contains(@class, "jftiEf")]',  # Common review container
            '//div[contains(@class, "MyEned")]',  # Another review container
            '//div[contains(@data-review-id, "")]',  # Reviews with IDs
            '//div[@role="article" and contains(@class, "fontBodyMedium")]',  # Article role reviews
            '//div[contains(@class, "gws-localreviews__google-review")]',  # Local reviews
            '//div[contains(@jsaction, "mouseover:pane.review")]'  # Interactive reviews
        ]
        
        review_elements = None
        
        # Try different selectors
        for selector in review_selectors:
            elements = page.locator(selector)
            count = await elements.count()
            if count > 0:
                logging.info(f"Found {count} review elements with selector: {selector}")
                review_elements = elements
                break
        
        if not review_elements:
            logging.warning("No review elements found with any selector")
            
            # Debug: Let's see what elements are actually on the page
            try:
                logging.info("Debugging: Looking for any div elements containing review-related text...")
                debug_elements = page.locator('//div[contains(text(), "review") or contains(@class, "review") or contains(@aria-label, "review")]')
                debug_count = await debug_elements.count()
                logging.info(f"Found {debug_count} elements with 'review' in text/class/aria-label")
                
                # Also check for any elements with star ratings
                star_elements = page.locator('//*[contains(@aria-label, "star") or contains(@aria-label, "Star") or contains(text(), "★")]')
                star_count = await star_elements.count()
                logging.info(f"Found {star_count} elements with star ratings")
                
                # Try to get the page HTML structure for debugging
                if debug_count == 0 and star_count == 0:
                    body_html = await page.locator('body').inner_html()
                    # Log first 500 chars to see page structure
                    logging.debug(f"Page HTML structure: {body_html[:500]}...")
                    
            except Exception as e:
                logging.debug(f"Debug failed: {e}")
                
            return reviews
            
        # Scroll to load more reviews
        max_scrolls = 5
        for scroll_attempt in range(max_scrolls):
            try:
                current_count = await review_elements.count()
                logging.info(f"Found {current_count} reviews after scroll {scroll_attempt + 1}")
                
                if current_count >= 10 or scroll_attempt >= max_scrolls - 1:
                    break
                
                # Scroll down
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(2)
                
                # Re-count after scroll
                review_elements = page.locator(review_selectors[0])  # Use first working selector
                
            except Exception as e:
                logging.warning(f"Scroll attempt {scroll_attempt + 1} failed: {e}")
                continue
        
        # Extract individual reviews
        total_reviews = await review_elements.count()
        logging.info(f"Extracting data from {total_reviews} reviews...")
        
        for i in range(min(total_reviews, 20)):  # Limit to 20 reviews
            try:
                review_element = review_elements.nth(i)
                review_data = {}
                
                # Extract author name - try multiple selectors
                author_selectors = [
                    './/div[contains(@class, "d4r55")]',  # Common author class
                    './/span[contains(@class, "X43Kjb")]',  # Another author class
                    './/div[contains(@class, "TSUbDb")]//a',  # Author link
                    './/button[contains(@class, "WEGxnd")]',  # Author button
                    './/div[contains(@class, "YAp4Ce")]',  # New author class
                    './/a[contains(@href, "/maps/contrib/")]'  # Contributor link
                ]
                
                for auth_sel in author_selectors:
                    try:
                        author_element = review_element.locator(auth_sel)
                        if await author_element.count() > 0:
                            author_text = await author_element.first.inner_text()
                            if author_text and len(author_text.strip()) > 0:
                                review_data['author'] = author_text.strip()
                                logging.debug(f"Found author: {author_text.strip()}")
                                break
                    except Exception as e:
                        logging.debug(f"Author selector {auth_sel} failed: {e}")
                        continue
                
                # Extract rating - try multiple approaches
                try:
                    # Look for aria-label with star rating
                    rating_elements = review_element.locator('.//*[contains(@aria-label, "star") or contains(@aria-label, "Star")]')
                    if await rating_elements.count() > 0:
                        aria_label = await rating_elements.first.get_attribute("aria-label")
                        if aria_label:
                            rating_match = re.search(r'(\d+)', aria_label)
                            if rating_match:
                                review_data['rating'] = int(rating_match.group(1))
                    
                    # Alternative: look for star icons
                    if 'rating' not in review_data:
                        star_elements = review_element.locator('.//*[contains(@class, "kvMYJc")]')
                        review_data['rating'] = await star_elements.count()
                        
                except Exception as e:
                    logging.debug(f"Failed to extract rating for review {i + 1}: {e}")
                
                # Extract review text
                text_selectors = [
                    './/span[contains(@class, "wiI7pd")]',  # Main review text
                    './/div[contains(@class, "MyEned")]//span',  # Alternative text
                    './/span[contains(@data-expandable-section, "")]',  # Expandable text
                    './/div[contains(@class, "ZZ4bLe")]',  # New text class
                    './/span[contains(@jsaction, "click:pane.review.expandReview")]'  # Expandable review
                ]
                
                for text_sel in text_selectors:
                    try:
                        text_element = review_element.locator(text_sel)
                        if await text_element.count() > 0:
                            review_text = await text_element.first.inner_text()
                            if review_text and len(review_text.strip()) > 3:
                                review_data['text'] = review_text.strip()
                                logging.debug(f"Found review text: {review_text[:50]}...")
                                break
                    except Exception as e:
                        logging.debug(f"Text selector {text_sel} failed: {e}")
                        continue
                
                # Extract date
                date_selectors = [
                    './/span[contains(@class, "rsqaWe")]',
                    './/span[contains(@class, "dehysf")]',
                    './/div[contains(@class, "p2TkOb")]'
                ]
                
                for date_sel in date_selectors:
                    try:
                        date_element = review_element.locator(date_sel)
                        if await date_element.count() > 0:
                            date_text = await date_element.first.inner_text()
                            if date_text and len(date_text.strip()) > 0:
                                review_data['date'] = date_text.strip()
                                break
                    except:
                        continue
                
                # Only add review if we got some meaningful data
                if review_data.get('author') or review_data.get('text'):
                    # Set defaults for missing fields
                    review_data.setdefault('author', 'Anonymous')
                    review_data.setdefault('rating', 0)
                    review_data.setdefault('text', '')
                    review_data.setdefault('date', '')
                    
                    reviews.append(review_data)
                    logging.debug(f"Extracted review {len(reviews)}: {review_data.get('author', 'Unknown')}")
                    
            except Exception as e:
                logging.error(f"Failed to extract review {i + 1}: {e}")
                continue
        
        logging.info(f"Successfully extracted {len(reviews)} reviews")
        
    except Exception as e:
        logging.error(f"Error in extract_reviews: {e}")
    
    return reviews


# Synchronous wrapper for backward compatibility
def extract_reviews_sync(page) -> List[Dict]:
    """Synchronous wrapper for extract_reviews"""
    return asyncio.run(extract_reviews(page))