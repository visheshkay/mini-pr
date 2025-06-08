import json
import os

def load_qualitative_trait_keywords():
    filepath = os.path.join(os.path.dirname(__file__), 'qualitative_trait_mapping.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)



    
def load_quantitative_trait_keywords():
    filepath = os.path.join(os.path.dirname(__file__), 'quantitative_trait_mapping.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
