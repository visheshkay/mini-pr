import re
import pandas as pd

def find_accession_by_id(query, df):
    """
    Extracts the numeric part of the accession ID from a query and finds the matching accession in the dataset.
    Handles patterns like 'IS <digit>', 'ID <digit>', and 'identifier <digit>'.
    Returns matching rows from the dataset or a message if not found.
    """
    # Regex matches 'IS', 'ID', or 'identifier' followed by optional whitespace and digits
    match = re.search(r"\b(?:IS|ID|identifier)\s*(\d+)\b", query, re.IGNORECASE)

    if match:
        accession_id = int(match.group(1))
        results = df[df["ICRISAT accession identifier"] == accession_id] 
        # Check if results are not empty
        if not results.empty:
            return results[['ICRISAT accession identifier','Plant pigmentation','Seed color','Country Source']]
        else:
            return f"No matching accession found for the ID: {accession_id}"
    else:
        return "No valid accession ID found in query."

