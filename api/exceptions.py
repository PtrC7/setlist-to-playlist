import time
import threading
import requests
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Generic API Exceptions
class APIError(Exception):
    pass


class RateLimitError(APIError):
    pass


class NotFoundError(APIError):
    pass


class AuthenticationError(APIError):
    pass