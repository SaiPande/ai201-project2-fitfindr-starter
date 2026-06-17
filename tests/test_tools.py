import pytest

from tools import create_fit_card, search_listings, suggest_outfit


def test_search_listings_filters_by_description_and_price():
    results = search_listings("vintage graphic tee", size="M", max_price=30)

    assert isinstance(results, list)
    assert results, "Expected at least one matching listing"
    assert all(item["price"] <= 30 for item in results)
    assert any("graphic" in item["title"].lower() or "graphic" in item["description"].lower() for item in results)


def test_search_listings_returns_empty_for_no_match():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_suggest_outfit_empty_wardrobe_returns_general_advice():
    new_item = {
        "title": "Vintage Tee",
        "category": "tops",
        "colors": ["black"],
        "style_tags": ["vintage"],
    }
    wardrobe = {"items": []}

    suggestion = suggest_outfit(new_item, wardrobe)

    assert isinstance(suggestion, str)
    assert suggestion
    assert "Pair Vintage Tee" in suggestion or "Style Vintage Tee" in suggestion


def test_suggest_outfit_includes_wardrobe_items_when_available():
    new_item = {
        "title": "Y2K Baby Tee",
        "category": "tops",
        "colors": ["white"],
        "style_tags": ["y2k"],
    }
    wardrobe = {
        "items": [
            {"category": "bottoms", "name": "Wide Leg Jeans"},
            {"category": "shoes", "name": "Chunky Sneakers"},
        ]
    }

    suggestion = suggest_outfit(new_item, wardrobe)

    assert "Wide Leg Jeans" in suggestion or "Chunky Sneakers" in suggestion


def test_create_fit_card_returns_fallback_when_llm_fails(monkeypatch):
    from tools import _call_llm

    def fail_llm(*args, **kwargs):
        raise RuntimeError("LLM request failed")

    monkeypatch.setattr("tools._call_llm", fail_llm)

    outfit = "Pair the thrifted tee with wide leg jeans and white sneakers."
    new_item = {"title": "Vintage Tee", "price": 18.0, "platform": "depop"}

    caption = create_fit_card(outfit, new_item)

    assert isinstance(caption, str)
    assert "Just scored the Vintage Tee" in caption
    assert "depop" in caption


def test_create_fit_card_returns_error_for_missing_outfit():
    new_item = {"title": "Vintage Tee", "price": 18.0, "platform": "depop"}
    caption = create_fit_card("", new_item)
    assert caption == "I couldn't create a fit card because the outfit suggestion was missing."
