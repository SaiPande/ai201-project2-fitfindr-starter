# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:**

**Step 1 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Step 2 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Step 3 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Final output to user:**

---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | | |
| `suggest_outfit` | | |
| `create_fit_card` | | |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**

**One divergence from your spec, and why:**

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Full README — Agent design, tools, and demo

### Tool inventory (exact function signatures)
- `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`
     - Purpose: search the mock listings dataset for items matching a short natural-language description and optional size/price filters. Returns a sorted list of listing dicts or `[]` if nothing matches (no exception).
- `suggest_outfit(new_item: dict, wardrobe: dict) -> str`
     - Purpose: given a selected listing and the user's wardrobe (a dict with an `items` list), return a concise outfit suggestion string. If the wardrobe is empty, returns general styling advice. Never raises for normal missing/empty wardrobe inputs.
- `create_fit_card(outfit: str, new_item: dict) -> str`
     - Purpose: generate a short (2–4 sentence) shareable caption for the outfit. If `outfit` is empty or missing, returns a descriptive error string (no exception).

The three tools are implemented in `tools.py` and are intentionally independent so you can test them in isolation.

### Planning loop (how decisions are made)
The agent (in `agent.py`) follows a deterministic sequential planning loop using a single `session` dict to hold state. The loop steps are:
1. Parse the raw user query into a normalized `description`, optional `size`, and optional `max_price` (the `session['parsed']` map).
2. Call `search_listings(description, size, max_price)`.
      - If the call returns an empty list, the agent sets `session['error']` to a friendly message and stops. This avoids calling downstream tools with missing data.
3. Select the top search result (`session['selected_item']` = first listing) and call `suggest_outfit(selected_item, wardrobe)`.
4. Use the returned `outfit` string to call `create_fit_card(outfit, selected_item)`.
5. Populate `session['outfit_suggestion']` and `session['fit_card']` and return the session for the UI to display.

This structure makes the flow easy to reason about and test: each step reads only from the `session` and writes one or two well-defined keys.

### State management
The agent uses a single dictionary `session` containing these keys (canonical):
- `query`: raw user input string
- `parsed`: dict with `description`, `size`, `max_price`
- `search_results`: list of listing dicts (may be empty)
- `selected_item`: listing dict or `None`
- `wardrobe`: wardrobe dict provided by UI
- `outfit_suggestion`: string or `None`
- `fit_card`: string or `None`
- `error`: `None` or string describing a user-facing error

Each tool writes its outputs back into the `session`. The agent checks `session['error']` after each critical step to decide whether to continue.

### Error handling (per tool) — concrete examples
- `search_listings`
     - Failure mode: no matching items (empty result list).
     - Agent behavior: set `session['error']` to a helpful string and stop the planning loop.
     - Concrete command we ran during testing:
          ```powershell
          .venv\Scripts\python.exe -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
          ```
          Output: `[]`
     - Example observed agent session (no-results branch):
          ```json
          {
               "search_results": [],
               "selected_item": null,
               "outfit_suggestion": null,
               "fit_card": null,
               "error": "Sorry, I couldn't find any listings that match your request. Try a broader description, a different size, or a higher price."
          }
          ```

- `suggest_outfit`
     - Failure mode: wardrobe empty (no combinable items).
     - Agent behavior: returns general styling advice (string) rather than raising. This maintains a graceful UX for new users.
     - Concrete command we ran:
          ```powershell
          .venv\Scripts\python.exe -c "from tools import search_listings, suggest_outfit; from utils.data_loader import get_empty_wardrobe; results = search_listings('vintage graphic tee', None, 50); print(suggest_outfit(results[0], get_empty_wardrobe()))"
          ```
          Observed output (styling advice):
          "Pair Graphic Tee — 2003 Tour Bootleg Style with high-waisted jeans or wide-leg trousers and chunky white sneakers for a casual, vintage-inspired look. Add a leather belt or a crossbody bag to keep the outfit grounded."

- `create_fit_card`
     - Failure mode: `outfit` argument empty or missing.
     - Agent behavior: returns a descriptive message (no exception), e.g.:
          ```text
          I couldn't create a fit card because the outfit suggestion was missing.
          ```
     - Command used to validate:
          ```powershell
          .venv\Scripts\python.exe -c "from tools import search_listings, create_fit_card; results = search_listings('vintage graphic tee', None, 50); print(create_fit_card('', results[0]))"
          ```

### Spec reflection
One way `planning.md` helped: it forced a clear separation between parsing, search, suggestion, and caption-generation. That made unit-testing each piece simple and prevented accidental cross-dependencies.

One divergence from the original spec: rather than raising exceptions on empty inputs for `suggest_outfit`, I deliberately returned friendly strings for new-user workflows so the UI remains useful without forcing extra error dialogs.

### AI usage (what we asked the LLM and how we adapted the output)
We use the Groq LLM only as a fallback in two places (both in `tools.py`):
1. `suggest_outfit` — when the wardrobe exists but the deterministic rules don't produce a clear outfit, we send this prompt:
          - System: "You are a friendly styling assistant. Write concise outfit recommendations."
          - User: includes the item title, category, colors, style tags, and a semicolon-separated list of wardrobe item names and categories. The assistant is asked to "Suggest one or two outfit combinations that use the new item and the wardrobe pieces."
          - What the LLM produced: concise numbered or sentence-based outfit ideas. We validated outputs locally and added a final fallback string when the LLM call fails.
          - What we changed/overrode: we sanitize and limit token usage (`max_tokens=220`) and use our deterministic chooser first. The LLM is only used when deterministic rules can't produce options.

2. `create_fit_card` — we prompt the LLM to write a 2–4 sentence caption including item title, price, and platform. Example prompt snippet:
          - System: "You are a creative stylist who writes short social media captions for outfits."
          - User: includes `title`, `price_text`, `platform`, and the `outfit` suggestion.
          - What we produced: human-friendly captions, but we validate for non-empty output and fall back to a deterministic caption if the LLM returns empty or errors.

### Running the app (end-to-end)
1. Install dependencies and set your Groq API key in `.env`:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
echo GROQ_API_KEY=your_key_here > .env
```
2. Start the app:
```powershell
python app.py
```
3. Open the URL shown in the terminal (usually http://localhost:7860). Try an example query, e.g. "vintage graphic tee under $30" and select "Example wardrobe." You should see three populated panels: top listing, outfit suggestion, fit card.

I validated the UI programmatically with a local call to `handle_query()` during development; the happy-path output looked like this:
```
Graphic Tee — 2003 Tour Bootleg Style — L — $24.0 — good on depop
Pair Graphic Tee — 2003 Tour Bootleg Style with your Baggy straight-leg jeans, dark wash, Chunky white sneakers, Vintage black denim jacket. This keeps the outfit balanced and gives the new top a polished everyday look.
Just scored the Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Pair Graphic Tee — 2003 Tour Bootleg Style with your Baggy straight-leg jeans, dark wash, Chunky white sneakers, Vintage black denim jacket. This keeps the outfit balanced and gives the new top a polished everyday look.
```

### Demo recording instructions
I can't create a video file in this environment, but here are reproducible commands and a small helper script to run the demo and capture exact terminal outputs. Use these to record your 3–5 minute walkthrough.

1) Automated demo runner (created in repo as `demo_run.py`):
```bash
python demo_run.py
```
This script performs three interactions: a happy-path query, an empty-wardrobe suggestion, and a no-results search. It writes the outputs to `demo-outputs.txt`.

2) Screen recording (Windows, using ffmpeg):
```powershell
# Start server in one terminal:
python app.py

# In another terminal, record your screen for 180 seconds (adjust device/index as needed):
ffmpeg -f gdigrab -framerate 30 -i desktop -t 180 demo-recording.mp4
```
For macOS, use `-f avfoundation -i 1` or a GUI recorder. Narrate while you interact with the UI.

### Where to find demo assets
- `demo_run.py`: automates interactions and saves `demo-outputs.txt`.

---
If you want, I can also add an explicit pytest that asserts the agent stops early when `search_listings` returns empty (monkeypatching `search_listings`). Want me to add that test and commit it? 
