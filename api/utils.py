import time
import threading
import requests
import logging

from api.exceptions import APIError, RateLimitError, NotFoundError

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.max_requests = 2
        self.time_window = 1
        self.requests = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        with self.lock:
            now = time.time()

            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    self.requests.pop(0)

            self.requests.append(now)

class CacheManager:
    def __init__(self, default_ttl: 300):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            
            if time.time() - self.timestamps[key] > self.default_ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            return self.cache[key]
        
    def set(self, key, value, ttl = None):
        with self.lock:
            self.cache[key] = value
            self.timestamps[key] = time.time()

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()

class RequestHandler:
    def __init__(self, api_key, rate_limiter: RateLimiter, cache: CacheManager):
        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({
        "Accept": "application/json",
        "x-api-key": api_key,
        })
        self.base_url = "https://api.setlist.fm/rest/1.0"

    def make_request(self, endpoint, params = None, use_cache = True, max_retries = 3):
        cache_key = f"{endpoint}:{str(sorted((params or {}).items()))}"

        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_result
            
        for attempt in range(max_retries):
            try:
                self.rate_limiter.wait_if_needed()

                url = f"{self.base_url}/{endpoint.lstrip('/')}"

                logger.info(f"Making request to: {url} (attempt {attempt + 1})")
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {endpoint}")
                
                response.raise_for_status()
                result = response.json()

                if use_cache:
                    self.cache.set(cache_key, result)

                return result
            
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise APIError(f"Request timeout after {max_retries} attempts")
                time.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise APIError(f"Request failed: {e}")
                time.sleep(2 ** attempt)

        raise APIError("max retries exceeded")
