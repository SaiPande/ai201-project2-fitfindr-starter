"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

# ── session state ─────────────────────────────────────────────────────────────

# _new_session: builds the shared session state for a single interaction.
# This dictionary tracks the original query, parsed slots, tool outputs,
# the selected thrift listing, the provided wardrobe, and any error.
def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── planning helpers ─────────────────────────────────────────────────────────

# _extract_size: extracts a user-specified size token from the query.
# It looks for explicit "size <value>" phrases and common standalone sizes.
def _extract_size(query: str) -> str | None:
    size_match = re.search(r"\bsize\s*([A-Za-z0-9]{1,3})\b", query, re.IGNORECASE)
    if size_match:
        return size_match.group(1).upper()

    token_match = re.search(r"\b(XXS|XS|S|M|L|XL|XXL|XXXL|\d{1,2})\b", query, re.IGNORECASE)
    if token_match:
        return token_match.group(1).upper()

    return None


# _extract_max_price: parses numeric budget constraints from the query.
# Supports patterns like "under $30", "below 40", "up to 50", or "$45".
def _extract_max_price(query: str) -> float | None:
    price_patterns = [
        r"under\s*\$?\s*(\d+(?:\.\d+)?)",
        r"below\s*\$?\s*(\d+(?:\.\d+)?)",
        r"up to\s*\$?\s*(\d+(?:\.\d+)?)",
        r"\$\s*(\d+(?:\.\d+)?)",
    ]
    for pattern in price_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


# _clean_description: removes size and price phrases so the remaining text
# is a clean item description for search relevance matching.
def _clean_description(query: str) -> str:
    cleaned = re.sub(r"\bsize\s*[A-Za-z0-9]{1,3}\b", "", query, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(under|below|up to)\s*\$?\s*\d+(?:\.\d+)?\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\$\s*\d+(?:\.\d+)?", "", cleaned)
    return " ".join(cleaned.split()).strip()


# ── planning loop ─────────────────────────────────────────────────────────────

# run_agent: orchestrates the sequential tool pipeline.
# It parses the query, calls search_listings, then suggest_outfit,
# then create_fit_card, storing each output in session and aborting on error.
def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    session = _new_session(query, wardrobe)

    description = _clean_description(query or "")
    size = _extract_size(query or "")
    max_price = _extract_max_price(query or "")

    session["parsed"] = {
        "description": description or query.strip(),
        "size": size,
        "max_price": max_price,
    }

    search_results = search_listings(
        description=session["parsed"]["description"],
        size=session["parsed"]["size"],
        max_price=session["parsed"]["max_price"],
    )
    session["search_results"] = search_results

    if not search_results:
        session["error"] = (
            "Sorry, I couldn't find any listings that match your request. "
            "Try a broader description, a different size, or a higher price."
        )
        return session

    session["selected_item"] = search_results[0]

    outfit_suggestion = suggest_outfit(session["selected_item"], session["wardrobe"])
    if not outfit_suggestion or not outfit_suggestion.strip():
        session["error"] = (
            "I couldn't generate an outfit suggestion from the selected item. "
            "Please try a different query."
        )
        return session

    session["outfit_suggestion"] = outfit_suggestion

    fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    if not fit_card or not fit_card.strip():
        session["error"] = (
            "I couldn't create a fit card from this suggestion. Please try again."
        )
        return session

    session["fit_card"] = fit_card
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
