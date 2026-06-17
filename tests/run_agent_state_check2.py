import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agent import run_agent
from utils.data_loader import get_example_wardrobe
from tools import suggest_outfit, create_fit_card

wardrobe = get_example_wardrobe()

print('=== Happy path ===')
session = run_agent('looking for a vintage graphic tee under $30', wardrobe)
print('search_results length:', len(session['search_results']))
print('selected_item equals top search result:', session['selected_item'] == session['search_results'][0] if session['search_results'] else 'no results')

# Recompute outfit from the selected item using the tool directly
if session['selected_item']:
    outfit_again = suggest_outfit(session['selected_item'], wardrobe)
    print('outfit_again == session[outfit_suggestion]:', outfit_again == session['outfit_suggestion'])
    card_again = create_fit_card(session['outfit_suggestion'], session['selected_item'])
    print('card_again == session[fit_card]:', card_again == session['fit_card'])
else:
    print('No selected item in session')

print('\n=== No-results path ===')
session2 = run_agent('designer ballgown size XXS under $5', wardrobe)
print('error present:', session2.get('error') is not None)
print('fit_card is None:', session2.get('fit_card') is None)
print('search_results length:', len(session2.get('search_results', [])))
