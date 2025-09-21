import spacy
from spacy.matcher import Matcher
import re

# Load SpaCy English model
nlp = spacy.load("en_core_web_sm")

# Initialize matcher
matcher = Matcher(nlp.vocab)

# Define trait keywords
trait_mapping = {
    "temperature": ["temperature", "temp"],
    "rainfall": ["rainfall", "precipitation"],
    "humidity": ["humidity", "humid"]
}

# Define crop keywords
crop_mapping = {
    "chickpea": ["chickpea", "chick pea", "chick-pea", "garbanzo", "ceci"],
    "sorghum": ["sorghum", "jowar", "milo"],
    "all": ["all", "any", "both"]
}

# Add matcher patterns for trait keywords
for trait, keywords in trait_mapping.items():
    for keyword in keywords:
        pattern = [{"LOWER": keyword.lower()}]
        matcher.add(trait, [pattern])

# Function to extract number or range with improved regex
def extract_num_range(text):
    # First, try to find ranges with units
    unit_patterns = [
        # "10 to 50 %" or "10-50 %" (range with unit at end)
        r"(\d+\.?\d*)\s*(?:[-–to]+\s*(\d+\.?\d*))\s*(mm|°C|%|degrees?)",
        # "100 mm to 1000 mm" (unit at both ends)
        r"(\d+\.?\d*)\s*(mm|°C|%|degrees?)\s*(?:[-–to]+\s*(\d+\.?\d*)\s*(?:mm|°C|%|degrees?)?)",
        # "100 mm to 1000" (unit at beginning)
        r"(\d+\.?\d*)\s*(mm|°C|%|degrees?)\s*(?:[-–to]+\s*(\d+\.?\d*))",
        # "in the range of 10 to 50 %"
        r"in\s+the\s+range\s+of\s+(\d+\.?\d*)\s*(?:[-–to]+\s*(\d+\.?\d*))\s*(mm|°C|%|degrees?)"
    ]
    
    for pattern in unit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num1 = float(match.group(1))
            num2 = float(match.group(2)) if len(match.groups()) > 1 and match.group(2) else None
            unit = match.group(3) if len(match.groups()) > 2 and match.group(3) else None
            if num2 is not None:  # We have a range
                return (num1, num2, unit)
            else:  # Single value with unit
                return (num1, num1, unit)
    
    # If no unit found, try to find simple ranges without units
    # This is crucial for queries like "humidity 10 to 60"
    # But we need to be more careful about false matches
    
    # First, check if there are min/max keywords in the text
    has_min_max = bool(re.search(r'\b(min|max|minimum|maximum)\b', text, re.IGNORECASE))
    
    if has_min_max:
        # If min/max keywords are present, we need to handle them separately
        # Don't try to extract ranges here as they might be false matches
        return None
    
    # If no min/max keywords, then look for simple ranges
    range_patterns = [
        # "10 to 60" or "10-60" (simple range)
        r"(\d+\.?\d*)\s*(?:[-–to]+\s*(\d+\.?\d*))",
        # Single number
        r"(\d+\.?\d*)"
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num1 = float(match.group(1))
            num2 = float(match.group(2)) if len(match.groups()) > 1 and match.group(2) else None
            if num2 is not None:  # We have a range
                return (num1, num2, None)
            else:  # Single value
                return (num1, num1, None)
    
    return None

# Function to detect keywords like "minimum", "maximum", "at least"
def extract_range_keywords(text):
    text_lower = text.lower()
    keywords = {
        "min": ["minimum", "min", "at least", "atleast", "from"],
        "max": ["maximum", "max", "up to", "upto", "less than", "lessthan"]
    }
    
    detected = {}
    for range_type, keyword_list in keywords.items():
        for keyword in keyword_list:
            if keyword in text_lower:
                detected[range_type] = keyword
                break
    
    return detected

# Function to detect crop from query
def extract_crop(query):
    query_lower = query.lower()
    
    # Check for specific crops first
    for crop, keywords in crop_mapping.items():
        if crop != "all":  # Skip "all" for now
            for keyword in keywords:
                if keyword in query_lower:
                    return crop
    
    # If no specific crop found, return "all"
    return "all"

# Function to find number/range after trait with keyword support
def extract_traits_with_ranges(query):
    doc = nlp(query)
    matches = matcher(doc)
    extracted_traits = {}
    
    # Extract crop information
    crop = extract_crop(query)
    if crop != "all":
        extracted_traits["crop"] = crop

    for match_id, start, end in matches:
        trait_name = nlp.vocab.strings[match_id]
        span = doc[start:end]
        
        # Create a more focused context around the trait keyword
        # Look for the trait name and numbers in a more targeted way
        # Use a smaller, more focused context to avoid cross-contamination
        context_start = max(0, start-1)  # Only 1 token before
        context_end = min(len(doc), end+4)  # Only 4 tokens after
        context_tokens = doc[context_start:context_end]
        context_text = " ".join([token.text for token in context_tokens])
        
        # Extract range keywords specific to this trait's context
        trait_range_keywords = extract_range_keywords(context_text)
        
        # Try to extract range from the focused context
        range_info = extract_num_range(context_text)
        
        if range_info:
            num1, num2, unit = range_info
            
            # Handle keyword-based ranges specific to this trait
            if "min" in trait_range_keywords and "max" not in trait_range_keywords:
                # "minimum 500 mm rainfall" -> set min to 500, max to full range
                extracted_traits[trait_name] = {
                    "min": num1,
                    "max": None,  # Will be set to full range in frontend
                    "unit": unit or None,
                    "keyword": "min"
                }
            elif "max" in trait_range_keywords and "min" not in trait_range_keywords:
                # "maximum 500 mm rainfall" -> set min to 0, max to 500
                extracted_traits[trait_name] = {
                    "min": None,  # Will be set to 0 in frontend
                    "max": num1,
                    "unit": unit or None,
                    "keyword": "max"
                }
            elif "min" in trait_range_keywords and "max" in trait_range_keywords:
                # Both min and max keywords found for this trait
                # We need to find both values
                min_match = re.search(rf"min\s+(\d+\.?\d*)", context_text, re.IGNORECASE)
                max_match = re.search(rf"max\s+(\d+\.?\d*)", context_text, re.IGNORECASE)
                
                if min_match and max_match:
                    min_val = float(min_match.group(1))
                    max_val = float(max_match.group(1))
                    extracted_traits[trait_name] = {
                        "min": min_val,
                        "max": max_val,
                        "unit": unit or None
                    }
                else:
                    # Fallback to normal range
                    extracted_traits[trait_name] = {
                        "min": num1,
                        "max": num2 if num2 else num1,
                        "unit": unit or None
                    }
            else:
                # Normal range or single value
                extracted_traits[trait_name] = {
                    "min": num1,
                    "max": num2 if num2 else num1,
                    "unit": unit or None
                }
        else:
            # extract_num_range returned None, which might mean min/max keywords are present
            # Try to extract min/max values directly
            if "min" in trait_range_keywords or "max" in trait_range_keywords:
                min_match = re.search(rf"min\s+(\d+\.?\d*)", context_text, re.IGNORECASE)
                max_match = re.search(rf"max\s+(\d+\.?\d*)", context_text, re.IGNORECASE)
                
                if min_match and max_match:
                    # Both min and max found
                    min_val = float(min_match.group(1))
                    max_val = float(max_match.group(1))
                    extracted_traits[trait_name] = {
                        "min": min_val,
                        "max": max_val,
                        "unit": None
                    }
                elif min_match:
                    # Only min found
                    min_val = float(min_match.group(1))
                    extracted_traits[trait_name] = {
                        "min": min_val,
                        "max": None,
                        "unit": None,
                        "keyword": "min"
                    }
                elif max_match:
                    # Only max found
                    max_val = float(max_match.group(1))
                    extracted_traits[trait_name] = {
                        "min": None,
                        "max": max_val,
                        "unit": None,
                        "keyword": "max"
                    }
            else:
                # No min/max keywords, try to find simple ranges
                # Look for patterns like "10 to 60" without min/max keywords
                # But be more careful about the context - only look for ranges that are clearly associated with this trait
                simple_range_match = re.search(r"(\d+\.?\d*)\s*(?:[-–to]+\s*(\d+\.?\d*))", context_text, re.IGNORECASE)
                if simple_range_match:
                    num1 = float(simple_range_match.group(1))
                    num2 = float(simple_range_match.group(2))
                    extracted_traits[trait_name] = {
                        "min": num1,
                        "max": num2,
                        "unit": None
                    }

    return extracted_traits
