import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agent import run_agent
import agent as agent_mod
from utils.data_loader import get_example_wardrobe

record = {}

def make_wrapper(original):
    def wrapper(new_item, wardrobe):
        record['called'] = True
        record['arg_id'] = id(new_item)
        record['arg_copy'] = new_item
        return original(new_item, wardrobe)
    return wrapper

# Wrap agent's suggest_outfit so we can capture the argument passed during run_agent
agent_mod.suggest_outfit = make_wrapper(agent_mod.suggest_outfit)

print('=== Running happy path check ===')
session = run_agent("looking for a straight leg khaki trousers under $40", get_example_wardrobe())
sel = session['selected_item']
print('selected_item id:', id(sel))
print('wrapped suggest_outfit saw id:', record.get('arg_id'))
print('arg equals selected_item (==):', record.get('arg_copy') == sel)
print('arg is selected_item (is):', record.get('arg_copy') is sel)
print('\nsession keys:', {k: type(v).__name__ for k,v in session.items()})
print('\noutfit_suggestion:', session.get('outfit_suggestion'))
print('\nfit_card:', session.get('fit_card'))

# Now verify no-results path does not call suggest_outfit
record.clear()
agent_mod.suggest_outfit = make_wrapper(agent_mod.suggest_outfit)
print('\n=== Running no-results path check ===')
session2 = run_agent("designer ballgown size XXS under $5", agent_mod.__import__('utils.data_loader').get_example_wardrobe())
print('error present:', session2.get('error') is not None)
print('fit_card is None:', session2.get('fit_card') is None)
print('suggest_outfit called during no-results path?:', record.get('called', False))
