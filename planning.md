# FitFindr — planning.md

<<<<<<< HEAD
> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools to generate your implementation.
> The planning content below is intentionally specific so the implementation is unambiguous.
=======
> FitFindr searches marketplace listings to find items that match a user's size, budget, and style preferences. When a matching item is found, it pairs it with pieces from the user's existing wardrobe to recommend a complete outfit and generate a social media caption. If the search returns no results, the process stops and provides the user with suggestions to adjust their criteria.
>>>>>>> 438ba0f5db96121e0fe3211c165a7956877f7ea4

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock thrift listings dataset for items that satisfy the user's desired description and optional filters, then ranks matching items by relevance.

**Input parameters:**
- `description` (str): A normalized search query phrase such as "vintage graphic tee" or "black combat boots". This is the core item description used for relevance matching.
- `size` (str | None): Optional size filter like "S", "M", "8", "XXS". When provided, the tool keeps listings whose `size` field contains the requested value case-insensitively.
- `max_price` (float | None): Optional upper price limit. When provided, the tool keeps listings with `price <= max_price`.

**What it returns:**
A list of listing dictionaries sorted with the best match first. Each result dictionary includes:
- `id` (str)
- `title` (str)
- `description` (str)
- `category` (str)
- `style_tags` (list[str])
- `size` (str)
- `condition` (str)
- `price` (float)
- `colors` (list[str])
- `brand` (str or None)
- `platform` (str)

If no item matches, it returns an empty list.

**What happens if it fails or returns nothing:**
If the returned list is empty, the agent should set `session["error"]` to a helpful no-results message and stop the planning loop before calling any later tools.

---

### Tool 2: suggest_outfit

**What it does:**
Produces one or two styling recommendations that pair the selected thrift listing with items in the user's wardrobe. If the wardrobe is empty, it produces general styling advice for the new item.

**Input parameters:**
- `new_item` (dict): The selected thrift listing dictionary returned by `search_listings`.
- `wardrobe` (dict): A wardrobe object containing an `items` list of wardrobe item dictionaries.

**What it returns:**
A non-empty string describing styling options. If the wardrobe contains items, the string should mention at least one wardrobe item or item category by name or function (e.g., "high-waisted jeans", "chunky sneakers"). If the wardrobe is empty, the string should still provide useful, general outfit guidance.

**What happens if it fails or returns nothing:**
If the tool returns an empty string or whitespace only, the agent should set `session["error"]` to a message explaining the outfit suggestion could not be generated and terminate the flow.

---

### Tool 3: create_fit_card

**What it does:**
Generates a short social-media-style caption for the selected thrift item and the proposed outfit.

**Input parameters:**
- `outfit` (str): The outfit recommendation string returned by `suggest_outfit`.
- `new_item` (dict): The selected thrift listing dictionary.

**What it returns:**
A 2–4 sentence caption-like string. The caption should:
- mention the item name or title once,
- mention the price once,
- mention the platform once,
- reflect the outfit's vibe,
- sound natural and casual.

If the outfit input is invalid, the tool should return a descriptive failure string rather than raise an error.

**What happens if it fails or returns nothing:**
If the tool returns an empty string, the agent should set `session["error"]` to a fit-card failure message and terminate. If it returns a descriptive status message, the agent may pass that string back as `fit_card` if it is non-empty.

---

### Additional Tools (if any)

No additional tools are required for this version of FitFindr.

---

## Planning Loop

**How does your agent decide which tool to call next?**
The agent uses a deterministic sequential planning loop. It does not choose between alternate tools, but it does validate outcomes after each tool and returns early if a failure is detected.

1. Create a new session dictionary containing the original `query`, the provided `wardrobe`, and empty placeholders for parsed data, tool results, and errors.
2. Parse the user's query to extract:
   - `description`: the remaining text after removing recognized price and size phrases.
   - `size`: optional size extracted from patterns like `size M`, `size 8`, or simple standalone sizes such as `XXS`, `L`, `10`.
   - `max_price`: optional numeric upper bound extracted from patterns like `under $30`, `below 40`, `<= 50`, or `$45`.
3. Store `description`, `size`, and `max_price` under `session["parsed"]`.
4. Call `search_listings(description, size, max_price)`.
5. If `search_results` is empty, set `session["error"]` to a friendly no-results message and return immediately.
6. Otherwise, set `session["selected_item"]` to the first result in `search_results`.
7. Call `suggest_outfit(session["selected_item"], session["wardrobe"])`.
8. If `outfit_suggestion` is empty or whitespace, set `session["error"]` to an outfit-suggestion failure message and return immediately.
9. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
10. If `fit_card` is empty or whitespace, set `session["error"]` to a fit-card failure message and return immediately.
11. Return the completed session.

The loop is done when `create_fit_card` returns successfully or when any step produces an error.

---

## State Management

**How does information from one tool get passed to the next?**
The agent stores all interaction state in a single `session` dictionary. Fields include:
- `query`: original user query text.
- `parsed`: a dict with `description`, `size`, and `max_price` extracted from the query.
- `search_results`: list of listing dictionaries returned by `search_listings`.
- `selected_item`: the top listing chosen for outfit generation.
- `wardrobe`: the provided wardrobe dict.
- `outfit_suggestion`: the string returned by `suggest_outfit`.
- `fit_card`: the string returned by `create_fit_card`.
- `error`: a failure message when the agent ends early.

The tool sequence passes state explicitly:
- `search_listings` consumes `session["parsed"]`.
- `suggest_outfit` consumes `session["selected_item"]` and `session["wardrobe"]`.
- `create_fit_card` consumes `session["outfit_suggestion"]` and `session["selected_item"]`.

If any tool fails, `session["error"]` is populated and subsequent tools are skipped.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Set `session["error"]` to `"Sorry, I couldn't find any listings that match your request. Try a broader description, a different size, or a higher price."` and return immediately. |
| suggest_outfit | Wardrobe is empty | Return a general styling advice string for the new item instead of raising an error; do not set `session["error"]`. |
| create_fit_card | Outfit input is missing or incomplete | Return a descriptive fallback message if possible. If the caption is empty, set `session["error"]` to `"I couldn't create a fit card from this suggestion. Please try again."` and return immediately. |

---

## Architecture

```mermaid
flowchart TD
    U[User query] --> PL[Planning Loop]
    PL --> PARSE[Parse query → description, size, max_price]
    PARSE --> S1[search_listings(description, size, max_price)]
    S1 -->|no results| E1[Set session.error: no listings found]
    E1 --> RET[Return session]
    S1 -->|results found| SI[Set selected_item = top result]
    SI --> S2[suggest_outfit(selected_item, wardrobe)]
    S2 -->|empty outfit| E2[Set session.error: outfit suggestion failed]
    E2 --> RET
    S2 -->|non-empty outfit| OS[Store outfit_suggestion]
    OS --> S3[create_fit_card(outfit_suggestion, selected_item)]
    S3 -->|empty fit card| E3[Set session.error: fit card failed]
    E3 --> RET
    S3 -->|non-empty fit card| FC[Store fit_card]
    FC --> RET

    classDef error fill:#f8d7da,stroke:#d9534f,color:#721c24;
    class E1,E2,E3 error;
```

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**
- Tool: `search_listings`
  - AI tool: Copilot or ChatGPT.
  - Input: the `Tool 1: search_listings` block above, the existing `tools.py` stub, and `utils/data_loader.py`'s `load_listings()` contract.
  - Expected output: a Python function that loads all listings, optionally filters by `max_price` and `size`, computes a relevance score from keyword overlap with `description`, drops zero-score results, and returns the sorted list.
  - Verification: inspect the code to ensure it uses case-insensitive size matching, price filtering, keyword scoring, and returns an empty list when no matches exist. Then run the function with a size filter, a low-price query that should return empty results, and a broad query that should return at least one listing.
- Tool: `suggest_outfit`
  - AI tool: Copilot or ChatGPT.
  - Input: the `Tool 2: suggest_outfit` block above and the `tools.py` stub.
  - Expected output: a Python function that handles empty wardrobes by returning general styling advice and handles non-empty wardrobes by referencing wardrobe items in the output. It should return a non-empty string in both cases and never raise for an empty wardrobe.
  - Verification: check the source for explicit empty-wardrobe handling. Test the function with `get_empty_wardrobe()` and `get_example_wardrobe()` from `utils/data_loader.py`, verifying output exists and mentions either general styling or specific wardrobe categories.
- Tool: `create_fit_card`
  - AI tool: Copilot or ChatGPT.
  - Input: the `Tool 3: create_fit_card` block above and the `tools.py` stub.
  - Expected output: a Python function that validates `outfit`, includes item title, price, and platform in the prompt, and returns a 2–4 sentence caption. If the outfit input is missing, it should return a descriptive string instead of raising.
  - Verification: confirm the code checks `outfit` non-emptiness. Run the function with a sample outfit and listing to ensure it returns a non-empty caption string.

**Milestone 4 — Planning loop and state management:**
- AI tool: Copilot or ChatGPT.
- Input: the `Planning Loop`, `State Management`, and `Error Handling` sections above, plus the `Architecture` diagram.
- Expected output: a `run_agent()` implementation in `agent.py` that initializes the session, parses the query into `description`, `size`, and `max_price`, calls `search_listings`, checks for empty results, selects the top result, calls `suggest_outfit`, validates its output, calls `create_fit_card`, validates its output, and returns the session.
- Verification: run `agent.py` with the built-in CLI happy path and the no-results path. Confirm the session outputs match the expected flow: top listing, outfit string, fit card string, or an error message for no results.

---

## A Complete Interaction (Step by Step)

Use a specific example query and show the exact tool inputs and outputs.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent initializes a new session and parses the query. It extracts:
- `description`: "vintage graphic tee"
- `size`: `None` (no explicit size phrase found)
- `max_price`: `30.0`

**Step 2:**
The agent calls `search_listings("vintage graphic tee", None, 30.0)`. The tool loads the listing dataset, filters out any item priced over $30, scores remaining items by keyword overlap with "vintage graphic tee", and returns a sorted list of matching listing dictionaries.

**Step 3:**
The agent checks `search_results`. If the list is empty, it sets `session["error"]` to a no-results message and stops. Otherwise, it selects the first listing and stores it in `session["selected_item"]`.

**Step 4:**
The agent calls `suggest_outfit(selected_item, wardrobe)`. If the wardrobe has items, the tool returns a string that references wardrobe pieces or categories. If the wardrobe is empty, it returns general styling advice for the new item.

**Step 5:**
The agent validates `outfit_suggestion`. If the string is empty, it sets `session["error"]` and returns. Otherwise, it proceeds.

**Step 6:**
The agent calls `create_fit_card(outfit_suggestion, selected_item)`. The tool uses the item title, price, and platform to generate a 2–4 sentence caption-like string.

**Step 7:**
The agent validates `fit_card`. If it is empty, it sets `session["error"]` and returns.

**Final output to user:**
The user receives three outputs:
- `listing_text`: a human-readable summary of the top matching listing from `selected_item`, for example the title, price, size, condition, and platform.
- `outfit_suggestion`: the outfit guidance string returned by `suggest_outfit`.
- `fit_card`: the caption string returned by `create_fit_card`.

If the query returned no matching listings, the user instead receives an error string in the first output panel and empty strings for the other two outputs.
