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

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

### Tool inventory (exact function signatures)
- `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`
     - Purpose: search the mock listings dataset for items matching a short natural-language description and optional size/price filters.
     - Inputs:
         - `description` (`str`): natural language text describing the desired item.
         - `size` (`str | None`): optional size filter, e.g. `"M"` or `"XXL"`.
         - `max_price` (`float | None`): optional maximum price ceiling.
     - Output: A sorted list of listing dicts, or `[]` when no matches are found.
- `suggest_outfit(new_item: dict, wardrobe: dict) -> str`
     - Purpose: create a wardrobe-aware outfit suggestion for the selected thrift item.
     - Inputs:
         - `new_item` (`dict`): the selected listing dict from `search_listings`.
         - `wardrobe` (`dict`): wardrobe data with a top-level `items` list.
     - Output: A non-empty outfit suggestion or styling advice string.
- `create_fit_card(outfit: str, new_item: dict) -> str`
     - Purpose: generate a short social-media caption for the thrifted outfit.
     - Inputs:
         - `outfit` (`str`): the string produced by `suggest_outfit`.
         - `new_item` (`dict`): the selected listing dict.
     - Output: A caption string, or a descriptive fallback string when `outfit` is empty.

The three tools are implemented in `tools.py` and are intentionally independent so they can be tested in isolation.

---

## Planning loop

The agent in `agent.py` is a sequential planner with explicit conditional exits. It does not branch based on hidden state; it follows a fixed pipeline and stops early only on failures.

1. Parse the raw user query into `description`, `size`, and `max_price`.
   - `description` is the query cleaned of size and budget phrases.
   - `size` is extracted from explicit `size X` patterns or standalone tokens like `M`, `L`, `XXS`.
   - `max_price` is parsed from phrases like `under $30`, `below 40`, `up to 50`, or `$45`.
2. Call `search_listings(description, size, max_price)`.
   - If the result list is empty, the agent sets `session['error']` and returns immediately.
3. Set `session['selected_item']` to the top result.
4. Call `suggest_outfit(selected_item, wardrobe)`.
5. Call `create_fit_card(outfit, selected_item)`.
6. Return the completed `session` dict.

Because the planner writes intermediate results into the `session` dict and checks for errors after each critical step, the exact flow is easy to trace.

---

## State management approach

The planner uses one shared `session` dict as the interaction state container. It is initialized with `_new_session(query, wardrobe)` and updated as each tool runs.

Stored state fields:
- `query`: the original raw input string.
- `parsed`: a dict containing `description`, `size`, and `max_price`.
- `search_results`: the list returned by `search_listings`.
- `selected_item`: the chosen listing dict.
- `wardrobe`: the wardrobe dict from the UI.
- `outfit_suggestion`: the string returned by `suggest_outfit`.
- `fit_card`: the string returned by `create_fit_card`.
- `error`: a string describing a fatal failure, or `None`.

The tools themselves are stateless and receive only the values they need; the agent passes data between them via the `session` dict.

---

## Error handling and fail points

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings(description, size, max_price)` | No listings match the query filters | Set `session['error']` and stop the pipeline. Do not call `suggest_outfit` or `create_fit_card`.
| `suggest_outfit(new_item, wardrobe)` | Empty wardrobe or no structured category match | Return a general styling advice string instead of raising an exception. Planner continues with `create_fit_card`.
| `create_fit_card(outfit, new_item)` | Empty `outfit` string or LLM failure | Return a deterministic fallback caption or descriptive error string without throwing.

Concrete examples from testing:
- `search_listings('designer ballgown', size='XXS', max_price=5)` returned `[]`. This exercised the no-results branch and produced the UI error message:
  `Sorry, I couldn't find any listings that match your request. Try a broader description, a different size, or a higher price.`
- `suggest_outfit(selected_item, get_empty_wardrobe())` returned a safe styling response like `"Pair [item] with high-waisted jeans or wide-leg trousers..."` instead of failing.
- `create_fit_card('', selected_item)` returned:
  `I couldn't create a fit card because the outfit suggestion was missing.`

---

## Spec reflection

**One way `planning.md` helped during implementation:**
Writing out the plan first made it clear that query parsing, search filtering, outfit recommendation, and caption generation should each be separate responsibilities. That helped me implement and test the tools one at a time.

**One divergence from the spec, and why:**
The spec described tools as isolated units, but I introduced a shared `session` dict in `agent.py` to make state passing explicit and failure handling simpler. This was intentional because it preserves tool modularity while making the pipeline easier to debug.

---

## AI usage

AI is used only in two well-defined fallback roles.

1. `suggest_outfit` uses Groq when deterministic wardrobe matching does not yield a strong suggestion. The prompt includes the selected item details and the wardrobe item names/categories, and asks for one or two outfit combinations. I then validate the text and fall back to a deterministic string if the LLM fails.

2. `create_fit_card` uses Groq to write a 2–4 sentence caption that mentions the item title, price, platform, and outfit suggestion. If the model returns empty output or raises, the code uses a deterministic fallback caption.

These AI calls are intentionally limited to creative text generation; search/filter logic remains deterministic.

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There is no required file structure for your agent code — organize it however makes sense for your design.

---

## Running the app

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
3. Open the URL shown in the terminal (usually http://localhost:7860) and try a query like `"vintage graphic tee under $30"` with the example wardrobe.

---

## Interaction Walkthrough
[](https://github.com/SaiPande/ai201-project2-fitfindr-starter#interaction-walkthrough)

**User query:** `vintage graphic tee under $30`

**Step 1 — Tool called:**

- Tool: `search_listings`
- Input: parsed query description `vintage graphic tee`, `size=None`, `max_price=30`
- Why this tool: find candidate thrift listings matching the user's request before any styling or captioning
- Output: sorted `search_results` list of matching listing dicts

**Step 2 — Tool called:**

- Tool: `suggest_outfit`
- Input: `selected_item` = top search result, `wardrobe` = user wardrobe dict
- Why this tool: generate a wardrobe-aware outfit suggestion using the selected thrift item and existing wardrobe pieces
- Output: outfit suggestion string stored as `outfit_suggestion`

**Step 3 — Tool called:**

- Tool: `create_fit_card`
- Input: `outfit` suggestion string, `new_item` = selected listing dict
- Why this tool: create a short, shareable caption for the UI based on the selected item and suggested outfit
- Output: caption string stored as `fit_card`

**Final output to user:**

- the top listing summary
- a wardrobe-aware outfit suggestion
- a fit card caption ready for display

---

## Error Handling and Fail Points
[](https://github.com/SaiPande/ai201-project2-fitfindr-starter#error-handling-and-fail-points)

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query filters | Set `session['error']` and stop the pipeline; do not call `suggest_outfit` or `create_fit_card` |
| `suggest_outfit` | Empty wardrobe or no structured category match | Return general styling advice instead of raising; planner continues with `create_fit_card` |
| `create_fit_card` | Empty `outfit` string or LLM failure | Return a deterministic fallback caption or descriptive error string without throwing |

---

## Spec Reflection
[](https://github.com/SaiPande/ai201-project2-fitfindr-starter#spec-reflection)

**One way planning.md helped during implementation:**

Writing out the plan first made it clear that query parsing, search filtering, outfit recommendation, and caption generation should each be separate responsibilities. That helped me implement and test the tools one at a time.

**One divergence from your spec, and why:**

The spec described tools as isolated units, but I introduced a shared `session` dict in `agent.py` to make state passing explicit and failure handling simpler. This was intentional because it preserves tool modularity while making the pipeline easier to debug.

---

## Demo helper

Use the provided `demo_run.py` script to reproduce the core paths: happy path, empty wardrobe, and no-results search. It writes deterministic terminal output that is easy to use in a recorded demo.

 
