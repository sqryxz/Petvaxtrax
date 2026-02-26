"""
Web Cache Utility for PetVaxHK Research

Provides caching functionality for fetching and storing web content
for research purposes (HK government vaccination requirements).
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
.getLogger(__name)
logger = logging__)


class WebCache:
    """Simple file-based web cache with TTL support."""
    
    def __init__(self, cache_dir: str = "processing/web_cache", ttl_hours: int = 24):
        """
        Initialize the web cache.
        
        Args:
            cache_dir: Directory to store cached files
            ttl_hours: Time-to-live for cached content in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PetVaxHK-Research/1.0 (pet vaccine tracker research)"
        })
    
    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path from URL."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return self.cache_dir / f"{url_hash}.json"
    
    def _is_valid(self, cache_path: Path) -> bool:
        """Check if cached file is still valid."""
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            
            cached_at = datetime.fromisoformat(data["cached_at"])
            expires_at = cached_at + timedelta(hours=self.ttl_hours)
            return datetime.now() < expires_at
        except (json.JSONDecodeError, KeyError, ValueError):
            return False
    
    def get(self, url: str, force_refresh: bool = False) -> Optional[dict]:
        """
        Get content from cache or fetch from URL.
        
        Args:
            url: URL to fetch
            force_refresh: If True, ignore cache and fetch fresh
            
        Returns:
            Dict with 'content', 'cached_at', 'url' keys, or None on error
        """
        cache_path = self._get_cache_path(url)
        
        # Check cache first (unless force refresh)
        if not force_refresh and self._is_valid(cache_path):
            try:
                with open(cache_path, "r") as f:
                    data = json.load(f)
                logger.info(f"Cache hit: {url}")
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Cache read error: {e}")
        
        # Fetch from URL
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = {
                "url": url,
                "content": response.text,
                "content_type": response.headers.get("Content-Type", "text/html"),
                "status_code": response.status_code,
                "cached_at": datetime.now().isoformat(),
                "cache_ttl_hours": self.ttl_hours
            }
            
            # Save to cache
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Cached: {url}")
            return data
            
        except requests.RequestException as e:
            logger.error(f"Fetch error for {url}: {e}")
            
            # Try to return stale cache if available
            if cache_path.exists():
                try:
                    with open(cache_path, "r") as f:
                        data = json.load(f)
                    data["error"] = str(e)
                    data["stale"] = True
                    logger.warning(f"Returning stale cache for: {url}")
                    return data
                except (json.JSONDecodeError, IOError):
                    pass
            
            return None
    
    def clear(self, url: Optional[str] = None) -> int:
        """
        Clear cached content.
        
        Args:
            url: If provided, clear only this URL's cache. Otherwise clear all.
            
        Returns:
            Number of files cleared
        """
        if url:
            cache_path = self._get_cache_path(url)
            if cache_path.exists():
                cache_path.unlink()
                return 1
            return 0
        
        # Clear all
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count
    
    def stats(self) -> dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        valid_count = sum(1 for f in cache_files if self._is_valid(f))
        
        return {
            "total_entries": len(cache_files),
            "valid_entries": valid_count,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl_hours
        }


# Convenience function for CLI usage
def fetch_with_cache(url: str, cache_dir: str = "processing/web_cache") -> Optional[str]:
    """
    Simple function to fetch a URL with caching.
    
    Args:
        url: URL to fetch
        cache_dir: Cache directory path
        
    Returns:
        HTML content or None on error
    """
    cache = WebCache(cache_dir)
    result = cache.get(url)
    return result["content"] if result else None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: web_cache.py <url> [--clear]")
        sys.exit(1)
    
    url = sys.argv[1]
    cache = WebCache()
    
    if "--clear" in sys.argv:
        count = cache.clear(url if url != "--clear" else None)
        print(f"Cleared {count} cache entries")
    else:
        result = cache.get(url)
        if result:
            print(f"Cached: {result['cached_at']}")
            print(f"Status: {result.get('status_code', 'unknown')}")
            print(f"Content length: {len(result['content'])} chars")
        else:
            print("Failed to fetch")
            sys.exit(1)
