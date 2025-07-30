import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from .trait_loader import load_qualitative_trait_keywords


trait_keywords = load_qualitative_trait_keywords()

df = pd.read_csv("models/final_combined.csv", low_memory=False)
    
cols = ['ICRISAT accession identifier',
 'Race',
 'Plant pigmentation',
 'Basal tillers number',
 'Nodal tillering',
 'Midrib color',
 'Panicle compactness and shape',
 'Glume color',
 'Glume covering',
 'Seed color',
 'Seed lustre',
 'Seed subcoat',
 'Endosperm texture',
 'Thresability',
 'Shoot fly-rainy',
 'Shoot fly-postrainy',
 'Stem borer',
 'Anthracnose',
 'Grain mold',
 'Leaf blight',
 'Rust',
 'Strigol control',
 'Season of harvest',
 'Site of rejuvenation',
 'Date of storage',
 'Location',
 'No. of Seeds',
 'Type of container',
 'Containers',
 'Date tested',
 'MT_status',
 'Duplicate status',
 'Seed health status',
 'Accession identifier',
 'Crop',
 'DOI',
 'Alternate accession identifier',
 'Local name',
 'Genus',
 'Species',
 'Spauthor',
 'Subtaxa',
 'Subtauthor',
 'Cultivar name',
 'Biological status',
 'Collecting source',
 'Donor cooperator code',
 'Donor country',
 'Acquisition Date',
 'Collection Date',
 'Country Source',
 'Province',
 'Collection site',
 'Latitude',
 'Longitude',
 'Elevation',
 'FAO in trust',
 'Core',
 'Mini core',
 'Remarks',
 'Growth habit',
 'Flower color',
 'Dots on seed coat',
 'Seed shape',
 'Seed surface',
 'Ascochyta blight',
 'Colletotrichum blight',
 'Botrytis grey mold',
 'Pod borer',
 'Year of Characterization',
 'Genotype / Sequencing info',
 'SPAUTHOR',
 'SUBTAXA',
 'SUBTAUTHOR']
        
unique_values = {col: df[col].unique().tolist() for col in cols}
del unique_values['Collection site']
del unique_values['ICRISAT accession identifier']
del unique_values['Strigol control']
del unique_values['Accession identifier']
del unique_values['Alternate accession identifier']
del unique_values['DOI']
del unique_values['Local name']


allowed_values = {
    col: set(str(v).lower() for v in vals if pd.notna(v))
    for col, vals in unique_values.items()
}
print(allowed_values['Seed color'])
del unique_values['Glume color']
del unique_values['Flower color']
del unique_values['Midrib color']
del unique_values['Country Source']
del unique_values['Donor country']
del unique_values['Latitude']
del unique_values['Longitude']
del unique_values['Leaf blight']
del unique_values['Rust']
del unique_values['Anthracnose']
del unique_values['Grain mold']
del unique_values['Remarks']
del unique_values['Botrytis grey mold'] #'Botrytis grey mold': 'susceptible', 'Stem borer': 'susceptible', 'Colletotrichum blight': 'susceptible', 'Ascochyta blight': 'susceptible'
del unique_values['Pod borer']
del unique_values['Stem borer']
del unique_values['Ascochyta blight']
del unique_values['Colletotrichum blight']


all_cols = set(unique_values) | set(trait_keywords)

nlp = spacy.blank("en")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# build patterns: both the actual values and any synonyms
for col in all_cols:
    patterns = []
    # 1) exact allowed values
    if col in unique_values.keys():
        patterns += [nlp(str(v).lower()) for v in unique_values[col] if pd.notna(v)]
    # 2) synonyms for this column
    for syn in trait_keywords.get(col, []):
        patterns.append(nlp(syn.lower()))
    matcher.add(col, patterns)

def extract_traits(query):
    """
    - Finds any span that matches either an allowed value OR a synonym.
    - If the span is an actual allowed value, we record it.
    - If the span is a synonym, we *do not* record it as a value,
      but we note that the user is asking about that column, so we can
      look for the *next* allowed value in the doc.
    """
    doc = nlp(query.lower())
    matches = matcher(doc)
    traits = {}

    # First pass: record exact‐value matches
    for match_id, start, end in matches:
        col = nlp.vocab.strings[match_id]
        if col in traits:
            continue

        # Try to find the longest match starting at `start`
        max_end = end
        max_value = doc[start:end].text

        for new_end in range(end + 1, min(len(doc) + 1, end + 5)):  # check next up to 4 tokens
            candidate = doc[start:new_end].text.lower().strip()
            if candidate in allowed_values.get(col, ()):
                max_end = new_end
                max_value = candidate

        # Only accept if final candidate is in allowed values
        if max_value in allowed_values.get(col, ()):
            traits[col] = max_value

    # Second pass: handle synonyms that didn’t directly map to a value
    #     e.g. user said “pigmented” (synonym for Plant pigmentation)
    #     but we didn’t see “dark” or “red” etc. as values yet
    for match_id, start, end in matches:
        col = nlp.vocab.strings[match_id]
        span = doc[start:end].text
        if col in traits:
            continue
        # print(col, span)
        cont = ''
        if span not in allowed_values.get(col, ()):
            
            # that must have been a synonym; look immediately after it
            # for the next token that *is* in allowed_values[col]
            for tok in doc[end : end + 7]:  # look up to 5 tokens after
                if tok.text=='%' or tok.text=='-':   
                    cont=cont[:len(cont)-1]
                cont+=tok.text
                # print(allowed_values.get(col, ()))
                if tok.text.lower() in allowed_values.get(col, ()):
                    traits[col] = tok.text
                    break
                if cont in allowed_values.get(col, ()):
                    traits[col] = cont
                    break
                # print(cont)
                # print(tok.text=='-')
                if tok.text!='>' and tok.text!='-':
                    cont+=' '


    return traits




# Replace the following function with SQL Logic
    


def filter_textual_accessions( extracted_traits,num_df):
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
        return num_df
    filtered_df = num_df.copy()

    for trait, value in extracted_traits.items():
        if trait in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[trait].astype(str).str.lower() == value.lower()]

              


    return filtered_df
