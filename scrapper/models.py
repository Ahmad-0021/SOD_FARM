# models.py - NO REVIEWS VERSION with coordinates and website

from dataclasses import dataclass
from typing import Optional


@dataclass
class Place:
    """Represents a Google Maps place - NO REVIEWS."""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None  # Added image URL field
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    def __str__(self) -> str:
        return (
            f"Place(name='{self.name}', "
            f"address='{self.address}', "
            f"phone='{self.phone}', "
            f"website='{self.website}', "
            f"image_url='{self.image_url}', "
            f"rating={self.rating}, "
            f"reviews_count={self.reviews_count}, "
            f"coordinates=({self.latitude}, {self.longitude}))"
        )
    
    def to_dict(self) -> dict:
        """Convert Place to dictionary for easy serialization."""
        return {
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'website': self.website,
            'image_url': self.image_url,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'latitude': self.latitude,
            'longitude': self.longitude
        }
    
    def has_coordinates(self) -> bool:
        """Check if place has valid coordinates."""
        return (
            self.latitude is not None and 
            self.longitude is not None and
            -90 <= self.latitude <= 90 and 
            -180 <= self.longitude <= 180
        )
    
    def get_google_maps_url(self) -> Optional[str]:
        """Generate Google Maps URL from coordinates."""
        if self.has_coordinates():
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None
    
    def to_csv_row(self) -> list:
        """Convert to CSV row format."""
        return [
            self.name or '',
            self.address or '',
            self.phone or '',
            self.website or '',
            self.image_url or '',
            self.rating or '',
            self.reviews_count or '',
            self.latitude or '',
            self.longitude or ''
        ]
    
    @staticmethod
    def csv_headers() -> list:
        """Get CSV headers."""
        return [
            'name',
            'address', 
            'phone',
            'website',
            'image_url',
            'rating',
            'reviews_count',
            'latitude',
            'longitude'
        ]