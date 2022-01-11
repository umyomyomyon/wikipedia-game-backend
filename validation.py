import time
import requests
from typing import List

from bs4 import BeautifulSoup

from exceptions import URLValidationException


def get_wikipedia_page(url: str):
    res = requests.get(url).text
    time.sleep(1)
    return res


def validate_url(url: str, next_url: str):
    target = next_url.split('wikipedia.org')
    res = get_wikipedia_page(url)
    soup = BeautifulSoup(res, 'html.parser')
    return bool(soup.find_all(href=target))


def validate_urls(start: str, urls: List[str], goal: str):
    _urls = [start] + urls + [goal]
    for idx, url in enumerate(_urls):
        if idx == len(_urls) - 1:
            break
        next_url = _urls[idx + 1]
        is_valid = validate_url(url, next_url)
        if not is_valid:
            raise URLValidationException(url, next_url)
    return True

