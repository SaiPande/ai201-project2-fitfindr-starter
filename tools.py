"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

from utils.data_loader import load_listings

load_dotenv()

_DEFAULT_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-8b-8192")


# _get_groq_client: initializes the Groq SDK client using GROQ_API_KEY
# loaded from .env. Raises a failure if the library or API key is missing.
def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    if Groq is None:
        raise ImportError("groq is not installed. Install the dependency or use local fallback logic.")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 0]


# _call_llm: sends a chat prompt to Groq and returns the assistant's text.
# It validates that the response includes a choice and content, otherwise it raises.
def _call_llm(messages: list[dict], temperature: float = 0.85, max_tokens: int = 220) -> str:
    """Call the Groq chat completions API and return the assistant text."""
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            messages=messages,
            model=_DEFAULT_GROQ_MODEL,
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )
        if not getattr(response, "choices", None):
            raise ValueError("No choices returned from the LLM.")
        message = response.choices[0].message
        content = getattr(message, "content", None)
        if not content:
            raise ValueError("No content returned from the LLM response.")
        return content.strip()
    except Exception as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc


# ── Tool 1: search_listings ───────────────────────────────────────────────────

# search_listings: loads all mock listings, filters them by max_price and size,
# scores each remaining item by keyword overlap against the query description,
# and sorts results by relevance then price.
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform
    """
    listings = load_listings()
    normalized_description = _normalize_text(description or "")
    query_terms = _tokenize(normalized_description)

    filtered_listings = []
    for item in listings:
        if max_price is not None and item.get("price", float("inf")) > max_price:
            continue

        if size is not None:
            item_size = str(item.get("size", "")).lower()
            if size.lower() not in item_size:
                continue

        filtered_listings.append(item)

    if not query_terms:
        return sorted(filtered_listings, key=lambda item: (item.get("price", float("inf")), item.get("title", "")))

    scored_items = []
    for item in filtered_listings:
        target_text = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("description", "")),
                str(item.get("category", "")),
                " ".join(item.get("style_tags", [])),
                str(item.get("brand", "") or ""),
                " ".join(item.get("colors", [])),
            ]
        )
        target_tokens = _tokenize(target_text)
        score = 0
        for term in query_terms:
            score += target_tokens.count(term)
            score += 2 if term == item.get("category", "").lower() else 0
            if term in [tag.lower() for tag in item.get("style_tags", [])]:
                score += 1

        if score > 0:
            scored_items.append((score, item))

    scored_items.sort(key=lambda pair: (-pair[0], pair[1].get("price", float("inf")), pair[1].get("title", "")))
    return [item for score, item in scored_items]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

# suggest_outfit: builds a wardrobe-aware recommendation for the selected item.
# If the wardrobe is empty it returns general styling advice.
# If the wardrobe contains items, it selects matching categories and names
# to produce a concrete outfit sentence, with an LLM fallback for edge cases.
def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    item_title = new_item.get("title", "this piece")
    item_category = new_item.get("category", "").lower()
    item_colors = [str(color).lower() for color in new_item.get("colors", []) if color]
    item_style_tags = [str(tag).lower() for tag in new_item.get("style_tags", []) if tag]

    def choose_items(categories: list[str]) -> list[str]:
        selected = []
        for category in categories:
            for wardrobe_item in wardrobe_items:
                if wardrobe_item.get("category") == category and wardrobe_item.get("name") not in selected:
                    selected.append(wardrobe_item.get("name"))
                    break
        return selected

    if not wardrobe_items:
        if item_category == "tops":
            return (
                f"Pair {item_title} with high-waisted jeans or wide-leg trousers and chunky white sneakers for a casual, vintage-inspired look. "
                "Add a leather belt or a crossbody bag to keep the outfit grounded."
            )
        if item_category == "bottoms":
            return (
                f"Style {item_title} with a fitted tee or cropped knit top and finish with chunky sneakers or combat boots. "
                "Layer on a denim jacket or oversized sweatshirt for an easy everyday outfit."
            )
        if item_category == "outerwear":
            return (
                f"Wear {item_title} over a simple tee and straight-leg jeans for an effortless layered outfit. "
                "Finish with sneakers or boots and keep accessories minimal."
            )
        if item_category == "shoes":
            return (
                f"Let {item_title} anchor a relaxed outfit with jeans and a cozy knit top. "
                "Black boots work best with structured silhouettes and muted colors."
            )
        return (
            f"Style {item_title} with clean basics, neutral colors, and a single statement accessory. "
            "Keep the rest of the outfit simple so the new piece can stand out."
        )

    if item_category == "tops":
        bottoms = choose_items(["bottoms"])
        shoes = choose_items(["shoes"])
        outerwear = choose_items(["outerwear"])
        picks = []
        if bottoms:
            picks.append(bottoms[0])
        if shoes:
            picks.append(shoes[0])
        if outerwear:
            picks.append(outerwear[0])
        if picks:
            return (
                f"Pair {item_title} with your {', '.join(picks)}. "
                "This keeps the outfit balanced and gives the new top a polished everyday look."
            )
    if item_category == "bottoms":
        tops = choose_items(["tops"])
        shoes = choose_items(["shoes"])
        accessories = choose_items(["accessories"])
        picks = tops + shoes + accessories
        if picks:
            return (
                f"Style {item_title} with your {', '.join(picks)} for a laid-back, wearable outfit. "
                "The mix of easy layers and accessories will make the look feel complete."
            )
    if item_category == "outerwear":
        tops = choose_items(["tops"])
        bottoms = choose_items(["bottoms"])
        shoes = choose_items(["shoes"])
        picks = tops + bottoms + shoes
        if picks:
            return (
                f"Layer {item_title} over your {', '.join(picks[:2])} and finish with {picks[2] if len(picks) > 2 else 'clean sneakers'}. "
                "That combination keeps the look cozy while letting the jacket shine."
            )
    if item_category == "shoes":
        bottoms = choose_items(["bottoms"])
        tops = choose_items(["tops"])
        accessories = choose_items(["accessories"])
        picks = bottoms + tops + accessories
        if picks:
            return (
                f"Wear {item_title} with your {', '.join(picks[:2])}. "
                "The shoes will anchor the outfit and add a strong finishing touch."
            )

    if item_category == "accessories":
        tops = choose_items(["tops"])
        bottoms = choose_items(["bottoms"])
        if tops and bottoms:
            return (
                f"Use {item_title} to tie together your {tops[0]} and {bottoms[0]}. "
                "It will add a small but stylish detail to your everyday outfit."
            )

    if wardrobe_items:
        fallback_items = [w.get("name") for w in wardrobe_items if w.get("name")][:2]
        if fallback_items:
            return (
                f"Pair {item_title} with your {', '.join(fallback_items)} for a simple, put-together outfit. "
                "That makes the thrift find feel easy to wear right away."
            )

    # Fall back to LLM if the wardrobe exists but no structured outfit was generated.
    prompt = [
        {"role": "system", "content": "You are a friendly styling assistant. Write concise outfit recommendations."},
        {
            "role": "user",
            "content": (
                f"The customer wants to style this thrift find: {item_title}. "
                f"Item category: {item_category}. "
                f"Item colors: {', '.join(item_colors) or 'unspecified'}. "
                f"Style tags: {', '.join(item_style_tags) or 'none'}. "
                "The wardrobe contains these items: "
                + "; ".join([f'{w.get('name')} ({w.get('category')})' for w in wardrobe_items])
                + ". Suggest one or two outfit combinations that use the new item and the wardrobe pieces."
            ),
        },
    ]
    try:
        return _call_llm(prompt, temperature=0.85, max_tokens=220)
    except RuntimeError:
        return (
            f"Pair {item_title} with versatile wardrobe pieces in neutral tones. "
            "Keep the rest of the outfit simple so the thrift find can stand out."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

# create_fit_card: turns the outfit recommendation into a short caption.
# It prompts the LLM to generate a 2-4 sentence social-media style caption,
# and it includes a deterministic fallback if the LLM fails or returns empty.
def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
    """
    if not outfit or not outfit.strip():
        return "I couldn't create a fit card because the outfit suggestion was missing."

    title = new_item.get("title", "this find")
    price = new_item.get("price")
    platform = new_item.get("platform", "the marketplace")
    price_text = f"${price:.2f}" if isinstance(price, (int, float)) else "a great price"

    prompt = [
        {"role": "system", "content": "You are a creative stylist who writes short social media captions for outfits."},
        {
            "role": "user",
            "content": (
                f"Write a 2-4 sentence caption for this thrifted item: {title}. "
                f"Price: {price_text}. Platform: {platform}. "
                f"Outfit suggestion: {outfit.strip()}. "
                "Make it feel casual, authentic, and like a real OOTD post. "
                "Mention the item name, price, and platform naturally once each."
            ),
        },
    ]
    try:
        caption = _call_llm(prompt, temperature=0.95, max_tokens=150)
        if not caption or not caption.strip():
            raise RuntimeError("Empty caption from LLM")
        return caption.strip()
    except RuntimeError:
        return (
            f"Just scored the {title} for {price_text} on {platform}. "
            f"{outfit.strip()}"
        )
