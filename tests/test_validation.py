import pytest

from validation import validate_url, validate_urls
from exceptions import URLValidationException


def test_validate_url():
    url = "https://ja.wikipedia.org/wiki/World_Wide_Web"
    next_url = "https://ja.wikipedia.org/wiki/%E6%A4%9C%E7%B4%A2"

    is_valid = validate_url(url, next_url)
    assert is_valid is True

    next_url = "https://ja.wikipedia.org/wiki/NLS"
    is_valid = validate_url(url, next_url)
    assert is_valid is True

    next_url = "https://ja.wikipedia.org/wiki/Category:World_Wide_Web"
    is_valid = validate_url(url, next_url)
    assert is_valid is True


def test_validate_urls():
    start = "https://ja.wikipedia.org/wiki/World_Wide_Web"
    goal = "https://ja.wikipedia.org/wiki/%E5%8B%95%E7%9A%84%E8%A8%88%E7%94%BB%E6%B3%95"
    urls = [
        "https://ja.wikipedia.org/wiki/%E6%A4%9C%E7%B4%A2",
        "https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%AB%E3%82%B4%E3%83%AA%E3%82%BA%E3%83%A0"
    ]

    is_valid = validate_urls(start, urls, goal)
    assert is_valid is True


def test_validate_urls_failed():
    start = "https://ja.wikipedia.org/wiki/World_Wide_Web"
    goal = "https://ja.wikipedia.org/wiki/%E5%8B%95%E7%9A%84%E8%A8%88%E7%94%BB%E6%B3%95"
    urls = [
        "https://ja.wikipedia.org/wiki/%E6%A4%9C%E7%B4%A2",
        "https://ja.wikipedia.org/wiki/%E8%B2%AA%E6%AC%B2%E6%B3%95"
    ]
    with pytest.raises(URLValidationException):
        validate_urls(start, urls, goal)


def test_validate_urls_failed_message():
    start = "https://ja.wikipedia.org/wiki/World_Wide_Web"
    goal = "https://ja.wikipedia.org/wiki/%E5%8B%95%E7%9A%84%E8%A8%88%E7%94%BB%E6%B3%95"
    urls = [
        "https://ja.wikipedia.org/wiki/%E6%A4%9C%E7%B4%A2",
        "https://ja.wikipedia.org/wiki/%E8%B2%AA%E6%AC%B2%E6%B3%95"
    ]
    try:
        validate_urls(start, urls, goal)
    except URLValidationException as e:
        expect_message = 'https://ja.wikipedia.org/wiki/%E8%B2%AA%E6%AC%B2%E6%B3%95はhttps://ja.wikipedia.org/wiki/%E6%A4%9C%E7%B4%A2からたどれません'
        assert e.message == expect_message
