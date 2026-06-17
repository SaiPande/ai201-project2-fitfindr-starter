"""
demo_run.py

Automates three demo interactions and writes outputs to demo-outputs.txt.

Run with:
    python demo_run.py

This is intended to produce deterministic terminal output you can include in a recorded demo.
"""
from app import handle_query
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe
from tools import search_listings

cases = [
    ("Happy path: vintage tee", "vintage graphic tee under $30", "Example wardrobe"),
    ("Empty wardrobe: styling advice", "vintage graphic tee under $30", "Empty wardrobe (new user)"),
    ("No-results: impossible filters", "designer ballgown size XXS under $5", "Example wardrobe"),
]

lines = []
for title, query, wardrobe_choice in cases:
    lines.append(f"=== {title} ===")
    listing, outfit, fitcard = handle_query(query, wardrobe_choice)
    lines.append(f"Query: {query} | Wardrobe: {wardrobe_choice}")
    lines.append("--- Listing ---")
    lines.append(listing or "(none)")
    lines.append("--- Outfit ---")
    lines.append(outfit or "(none)")
    lines.append("--- Fit Card ---")
    lines.append(fitcard or "(none)")
    lines.append("")

with open("demo-outputs.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Wrote demo-outputs.txt with results for 3 demo cases.")
