import pandas as pd
import re
import spacy
from spacy.matcher import Matcher
from .trait_loader import load_quantitative_trait_keywords


# Trait-to-keyword mapping
trait_mapping = load_quantitative_trait_keywords()

df = pd.read_csv("models/final_combined.csv", low_memory=False)
# Load a SpaCy model (small English model)
nlp_num = spacy.load("en_core_web_sm")

# Initialize the Matcher
num_matcher = Matcher(nlp_num.vocab)

# Define synonyms for operators
operator_synonyms = {
    "between": ["between", "from", "ranging from", "in the range of", "in range of", "in between"],
    "less_than": ["less than", "lower than", "smaller than", "under", "below", "not exceeding", "at most", "no more than", "fewer than"],
    "greater_than": ["greater than", "more than", "higher than", "larger than", "above", "over", "exceeding", "at least", "no less than"],
    "equal_to": ["equal to", "exactly", "is", "equals", "of", "=", "precisely", "specifically"]
}


"""Set up the SpaCy matcher with patterns for each trait"""
for trait, keywords in trait_mapping.items():
    for keyword in keywords:
        # Handle multi-word keywords
        words = keyword.lower().split()
        base_pattern = [{"LOWER": word} for word in words]
            
        # Pattern for "between X and Y"
        for between_term in operator_synonyms["between"]:
            between_words = between_term.split()
            between_pattern = base_pattern.copy()
            # Add the "between" operator terms
            between_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            between_pattern.extend([{"LOWER": word} for word in between_words])
            between_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            between_pattern.append({"LIKE_NUM": True})  # First number
            between_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            between_pattern.extend([{"LOWER": word, "OP": "?"} for word in ["and", "to"]])  # "and" or "to" connector
            between_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            between_pattern.append({"LIKE_NUM": True})  # Second number
            between_pattern.append({"IS_ALPHA": True, "OP": "?"})  # Optional unit
            num_matcher.add(f"{trait}_between", [between_pattern])
            
        # Pattern for "less than X"
        for less_term in operator_synonyms["less_than"]:
            less_words = less_term.split()
            less_pattern = base_pattern.copy()
            less_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            less_pattern.extend([{"LOWER": word} for word in less_words])
            less_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            less_pattern.append({"LIKE_NUM": True})
            less_pattern.append({"IS_ALPHA": True, "OP": "?"})  # Optional unit
            num_matcher.add(f"{trait}_less_than", [less_pattern])
            
        # Pattern for "greater than X"
        for greater_term in operator_synonyms["greater_than"]:
            greater_words = greater_term.split()
            greater_pattern = base_pattern.copy()
            greater_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            greater_pattern.extend([{"LOWER": word} for word in greater_words])
            greater_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            greater_pattern.append({"LIKE_NUM": True})
            greater_pattern.append({"IS_ALPHA": True, "OP": "?"})  # Optional unit
            num_matcher.add(f"{trait}_greater_than", [greater_pattern])
            
        # Pattern for "equal to X"
        for equal_term in operator_synonyms["equal_to"]:
            equal_words = equal_term.split()
            equal_pattern = base_pattern.copy()
            equal_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            equal_pattern.extend([{"LOWER": word} for word in equal_words])
            equal_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            equal_pattern.append({"LIKE_NUM": True})
            equal_pattern.append({"IS_ALPHA": True, "OP": "?"})  # Optional unit
            num_matcher.add(f"{trait}_equal_to", [equal_pattern])
            
        # Pattern for direct number after keyword (no explicit operator)
            direct_pattern = base_pattern.copy()
            direct_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            direct_pattern.extend([{"IS_ALPHA": True, "OP": "*"}])  # Allow some words in between
            direct_pattern.append({"LIKE_NUM": True})
            direct_pattern.append({"IS_ALPHA": True, "OP": "?"})  # Optional unit
            num_matcher.add(f"{trait}_direct", [direct_pattern])
        # 1. Direct with any number of optional intermediate words
            direct_with_intermediates_pattern = base_pattern.copy()
            direct_with_intermediates_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            direct_with_intermediates_pattern.extend([{"IS_ALPHA": True, "OP": "*"}])  # Any intermediate words
            direct_with_intermediates_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            direct_with_intermediates_pattern.append({"LIKE_NUM": True})
            direct_with_intermediates_pattern.append({"IS_ALPHA": True, "OP": "?"})  # Optional unit (e.g., cm, g)
            num_matcher.add(f"{trait}_direct_anywords", [direct_with_intermediates_pattern])

            # 2. Direct with NO intermediate words (number immediately follows the trait keyword)
            direct_immediate_pattern = base_pattern.copy()
            direct_immediate_pattern.extend([{"IS_PUNCT": True, "OP": "*"}])
            direct_immediate_pattern.append({"LIKE_NUM": True})
            direct_immediate_pattern.append({"IS_ALPHA": True, "OP": "?"})  # Optional unit
            num_matcher.add(f"{trait}_direct_immediate", [direct_immediate_pattern])




def extract_num_traits(query):
    doc = nlp_num(query)
    matches = num_matcher(doc)

    extracted_traits = {}

    # Extended operator priority
    operator_priority = [
        "between", 
        "less_than", 
        "greater_than", 
        "equal_to", 
        "direct_anywords", 
        "direct_flexible", 
        "direct_immediate", 
        "direct"
    ]

    # Group matches by trait
    trait_matches = {}
    for match_id, start, end in matches:
        match_type = nlp_num.vocab.strings[match_id]
        parts = match_type.split('_')
        trait = parts[0]
        operator_type = '_'.join(parts[1:]) if len(parts) > 1 else "direct"

        if trait not in trait_matches:
            trait_matches[trait] = []

        trait_matches[trait].append((operator_type, doc[start:end]))

    # Process traits by operator priority
    for trait, matches in trait_matches.items():
        for op in operator_priority:
            for operator_type, span in matches:
                if operator_type != op:
                    continue

                text = span.text

                if operator_type == "between":
                    between_match = re.search(r"(\d+\.?\d*)\s*(?:and|to|-)\s*(\d+\.?\d*)", text)
                    if between_match:
                        value1 = float(between_match.group(1))
                        value2 = float(between_match.group(2))
                        extracted_traits[trait] = {
                            "operator": "between",
                            "value": [value1, value2]
                        }
                        break

                else:
                    num_match = re.search(r"(\d+\.?\d*)", text)
                    if num_match:
                        value = float(num_match.group(1))
                        extracted_traits[trait] = {
                            "operator": (
                                operator_type 
                                if operator_type not in ["direct", "direct_anywords", "direct_flexible", "direct_immediate"]
                                else "equal_to"
                            ),
                            "value": value
                        }
                        break
            if trait in extracted_traits:
                break  # Already found highest-priority match

    return extracted_traits

def filter_accessions_by_ner( extracted_traits):
    """
    Filters germplasms based on extracted numerical values.

    Args:
        df (pd.DataFrame): The dataset containing accessions.
        extracted_traits (dict): Extracted trait-value pairs.
        tolerance (float): Percentage range for flexible matching.

    Returns:
        pd.DataFrame: Filtered accessions based on extracted traits.
    """

    if(len(extracted_traits)==0):
        return df
    filtered_df = df.copy()

    for trait, op_and_val in extracted_traits.items():
        operator = op_and_val["operator"]
        if operator=="between":
            value1 = op_and_val["value"][0]
            value2 = op_and_val["value"][1]
            if trait in df.columns:
              filtered_df = filtered_df[(filtered_df[trait] >= value1) & (filtered_df[trait] <= value2)]
        value = op_and_val["value"]
        if trait in df.columns:
            if operator == "greater_than":
                filtered_df = filtered_df[filtered_df[trait]>=value]
            elif operator == "less_than":
                filtered_df = filtered_df[filtered_df[trait]<=value]
            elif operator == "equal_to":
                filtered_df = filtered_df[filtered_df[trait]==value]
            
    return filtered_df
