from flask import Flask, request, jsonify
import pickle
import pandas as pd
from utils.idsearch import find_accession_by_id
from utils.numsearch import extract_num_traits
from utils.textsearch import (
    extract_traits,
)
from flask_cors import CORS
import pyodbc

def get_connection_sorghum():
    server = 'localhost,1433'
    database = 'Sorghum'
    driver = '/opt/homebrew/lib/libmsodbcsql.17.dylib;'
    username = 'sa'
    password = 'DB_Password'
    return pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=no;'
    )

def get_connection_chickpea():
    server = 'localhost,1433'
    database = 'Chickpea'
    driver = '/opt/homebrew/lib/libmsodbcsql.17.dylib;'
    username = 'sa'
    password = 'DB_Password'
    return pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=no;'
    )

characterisation_columns = [
    'ICRISAT accession identifier', 'Race', 'Plant height (cm)-postrainy',
    'Plant height (cm)-rainy', 'Plant pigmentation', 'Basal tillers number',
    'Nodal tillering', 'Midrib color', 'Days to flowering-postrainy',
    'Days to flowering-rainy', 'Panicle exertion (cm)', 'Panicle length (cm)',
    'Panicle width (cm)', 'Panicle compactness and shape', 'Glume color',
    'Glume covering', 'Seed color', 'Seed lustre', 'Seed subcoat',
    'Seed size (mm)', '100 Seed weight (g)', 'Endosperm texture',
    'Thresability', 'Shoot fly-rainy', 'Shoot fly-postrainy',
    'Downy mildew % (field)', 'Downy mildew % (glasshouse)', 'Stem borer',
    'Anthracnose', 'Grain mold', 'Leaf blight', 'Midge', 'Headbug', 'Rust',
    'Strigol control', 'Protein (%)', 'Lysine (%)', 'Remarks',
    'Year of characterization'
]

passport_columns = [
    'ICRISAT accession identifier', 'Accession identifier', 'Crop', 'DOI',
    'Mission code', 'Collectors number', 'Alternate accession identifier',
    'Local name', 'Genus', 'Species', 'Spauthor', 'Subtaxa', 'Subtauthor',
    'Cultivar name', 'Biological status', 'Collecting source',
    'Donor cooperator code', 'Donor country', 'Acquisition Date',
    'Collection Date', 'Country Source', 'Province', 'Collection site',
    'Latitude', 'Longitude', 'Elevation', 'Ec No', 'FAO in trust', 'Core',
    'Mini core', 'Remarks', 'Registered Date'
]

characterisation_columns_sorghum = [
    'ICRISAT accession identifier', 'Race', 'Plant height (cm)-postrainy',
    'Plant height (cm)-rainy', 'Plant pigmentation', 'Basal tillers number',
    'Nodal tillering', 'Midrib color', 'Days to flowering-postrainy',
    'Days to flowering-rainy', 'Panicle exertion (cm)', 'Panicle length (cm)',
    'Panicle width (cm)', 'Panicle compactness and shape', 'Glume color',
    'Glume covering', 'Seed color', 'Seed lustre', 'Seed subcoat',
    'Seed size (mm)', '100 Seed weight (g)', 'Endosperm texture',
    'Thresability', 'Shoot fly-rainy', 'Shoot fly-postrainy',
    'Downy mildew % (field)', 'Downy mildew % (glasshouse)', 'Stem borer',
    'Anthracnose', 'Grain mold', 'Leaf blight', 'Midge', 'Headbug', 'Rust',
    'Strigol control', 'Protein (%)', 'Lysine (%)', 'Remarks',
    'Year of characterization'
]

passport_columns_sorghum = [
    'ICRISAT accession identifier', 'Accession identifier', 'Crop', 'DOI',
    'Mission code', 'Collectors number', 'Alternate accession identifier',
    'Local name', 'Genus', 'Species', 'Spauthor', 'Subtaxa', 'Subtauthor',
    'Cultivar name', 'Biological status', 'Collecting source',
    'Donor cooperator code', 'Donor country', 'Acquisition Date',
    'Collection Date', 'Country Source', 'Province', 'Collection site',
    'Latitude', 'Longitude', 'Elevation', 'Ec No', 'FAO in trust', 'Core',
    'Mini core', 'Remarks', 'Registered Date'
]
characterisation_columns_chickpea = [
    "ICRISAT accession identifier",
    "Plant height (cm)",
    "Plant width (cm)",
    "Plant pigmentation",
    "Growth habit",
    "Basal primary branches number",
    "Apical primary branches number",
    "Basal secondary branches number",
    "Apical secondary branches number",
    "Tertiary branches number",
    "Days to flowering",
    "Flowering duration",
    "Flower color",
    "Days to maturity",
    "Pods per plant",
    "Seeds per pod",
    "Seed yield (Kg/ha)",
    "Seed color",
    "Dots on seed coat",
    "Seed shape",
    "Seed surface",
    "100 Seed weight (g)",
    "Protein (%)",
    "Wilt",
    "Ascochyta blight",
    "Colletotrichum blight",
    "Botrytis grey mold",
    "Pod borer",
    "Year of Characterization"
]

passport_columns_chickpea = [
    "ICRISAT accession identifier",
    "Accession identifier",
    "Crop",
    "Genotype / Sequencing info",
    "DOI",
    "Mission code",
    "Collectors number",
    "Alternate accession identifier",
    "Local name",
    "Genus",
    "Species",
    "SPAUTHOR",
    "SUBTAXA",
    "SUBTAUTHOR",
    "Cultivar name",
    "Biological status",
    "Collecting source",
    "Donor cooperator code",
    "Donor country",
    "Acquisition Date",
    "Collection Date",
    "Country Source",
    "Province",
    "Collection site",
    "Latitude",
    "Longitude",
    "Elevation",
    "Ec No",
    "FAO in trust",
    "Core",
    "Mini core",
    "Remarks",
    "Registered Date"
]

def run_query_for_db(query, values, conn_func):
    try:
        conn = conn_func()
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

app = Flask(__name__)
CORS(app)

# Load list and convert to DataFrame
df = pd.read_csv("models/MergedData.csv", low_memory=False)

# def get_final_results(query):
#     q=query.split(' ')
#     query = query.lower()

#     # Accession ID Based Shortlisting (Only return directly if 'IS' is present)
#     accession_results = find_accession_by_id(query, df)
#     is_accession_match = not isinstance(accession_results, str)

#     if ("IS" in q or "ID" in q or "id" in q or "Id" in q or "Is" in q) and is_accession_match:
#         return accession_results

#     # Numeric Value Based Shortlisting
#     numeric_traits = extract_num_traits(query,df)
#     numeric_results = filter_accessions_by_ner(numeric_traits, df)

#     # Textual Trait Based Shortlisting
#     traits = extract_traits(query, df)
#     filled_traits = fill_na_cols(traits, df)
#     structured_text = generate_structured_text_for_NER(filled_traits)
#     textual_results = test_text_search(structured_text, df, model, index)

#     results_list = []
#     if is_accession_match:
#         results_list.append(accession_results)
#     if not numeric_results.empty:
#         results_list.append(numeric_results)
#     if not textual_results.empty:
#         results_list.append(textual_results)

#     if results_list:
#         final_results = pd.concat(results_list).drop_duplicates(subset=["ICRISAT accession identifier"])
#         return final_results

#     return pd.DataFrame()  # Return empty DataFrame if nothing matches

def build_condition(column, operator, value):
    if operator == "equal_to":
        return f"[{column}] = ?", [value]
    elif operator == "less_than":
        return f"[{column}] < ?", [value]
    elif operator == "greater_than":
        return f"[{column}] > ?", [value]
    elif operator == "between":
        return f"[{column}] BETWEEN ? AND ?", value
    else:
        raise ValueError("Unsupported operator")

# def get_final_results(query):
#     # q = query.split(' ')
#     query = query.lower()

#     # --- Step 1: Get all types of results ---

#     # Accession ID Based Shortlisting (Only return directly if 'IS' is present)
#     accession_results = find_accession_by_id(query,df)
#     # Check if the result is a correct accession id or not after query from SQL
#     is_accession_match = not isinstance(accession_results, str)  # Check if valid DataFrame result


#     if ("is" in query or "id" in query or "identifier" in query) and is_accession_match:
#         return accession_results.to_dict(orient='records')

#     quantitative = extract_num_traits(query)

#     qualitative = extract_traits(query)

#     char_conditions = []
#     char_values = []
#     pass_conditions = []
#     pass_values = []

#     for column, val in qualitative.items():
#         if column in characterisation_columns:
#             char_conditions.append(f"c.[{column}] = ?")
#             char_values.append(val)
#         elif column in passport_columns:
#             pass_conditions.append(f"p.[{column}] = ?")
#             pass_values.append(val)

#     for column, info in quantitative.items():
#         try:
#             condition_str, vals = build_condition(column, info["operator"], info["value"])
#             if column in characterisation_columns:
#                 char_conditions.append(f"c.{condition_str}")
#                 char_values.extend(vals)
#             elif column in passport_columns:
#                 pass_conditions.append(f"p.{condition_str}")
#                 pass_values.extend(vals)
#         except Exception as e:
#             return jsonify({"error": str(e)}), 400

#     where_clause = ""
#     final_values = []

#     if char_conditions or pass_conditions:
#         where_clause = "WHERE "
#         all_conditions = []

#         if char_conditions:
#             all_conditions.extend(char_conditions)
#             final_values.extend(char_values)

#         if pass_conditions:
#             all_conditions.extend(pass_conditions)
#             final_values.extend(pass_values)

#         where_clause += " AND ".join(all_conditions)

#     query = f"""
#         SELECT TOP 100 *
#         FROM [dbo].[Characterization] c
#         JOIN [dbo].[Passport] p
#         ON c.[ICRISAT accession identifier] = p.[ICRISAT accession identifier]
#         {where_clause}
#     """
#     try:
#         conn = get_connection()
#         cursor = conn.cursor()
#         cursor.execute(query, tuple(final_values))
#         rows = cursor.fetchall()
#         columns = [column[0] for column in cursor.description]
#         results = [dict(zip(columns, row)) for row in rows]
#         return results if results else "No results found"
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

def get_final_results(query):
    # q = query.split(' ')
    query = query.lower()
    query = query.replace(",", " ")

    # --- Step 1: Get all types of results ---

    # Accession ID Based Shortlisting (Only return directly if 'IS' is present)
    accession_results = find_accession_by_id(query,df)
    # Check if the result is a correct accession id or not after query from SQL
    is_accession_match = not isinstance(accession_results, str)  # Check if valid DataFrame result

    if ("is" in query or "id" in query or "identifier" in query or "icc" in query) and is_accession_match:
        return accession_results.to_dict(orient='records')

    quantitative = extract_num_traits(query)
    qualitative = extract_traits(query)

    print(qualitative)
    print(quantitative)
    if(not qualitative and not quantitative):
        return "No valid traits found in query."

    # Collect all requested columns
    requested_columns = list(set(list(qualitative.keys()) + list(quantitative.keys())))
    
    # Add ICRISAT accession identifier to ensure we can join tables
    if "ICRISAT accession identifier" not in requested_columns:
        requested_columns.append("ICRISAT accession identifier")
    
    # Separate columns by table
    char_columns = [col for col in requested_columns if col in characterisation_columns]
    pass_columns = [col for col in requested_columns if col in passport_columns]
    all_columns = set(qualitative.keys()) | set(quantitative.keys())
    all_columns.add("ICRISAT accession identifier")
    print("All columns requested:", all_columns)

    def build_query(characterisation_columns, passport_columns, conn_func):
        def is_chickpea():
            return "chickpea" in conn_func.__name__.lower()

        def normalize_col(col):
            if is_chickpea() and "plant height" in col.lower():
                return "Plant height (cm)"
            return col

    # Normalize qualitative and quantitative trait keys for Chickpea
        
        
        char_columns = [col for col in all_columns if (col in characterisation_columns or col == "Plant height (cm)-postrainy" or col == "Plant height (cm)-rainy")]
        pass_columns = [col for col in all_columns if col in passport_columns]
        # print(f"Characterisation columns: {char_columns}")
        if is_chickpea():
            updated_qualitative = {}
            for k, v in qualitative.items():
                new_key = normalize_col(k)
                updated_qualitative[new_key] = v
            qualitative.clear()
            qualitative.update(updated_qualitative)

            updated_quantitative = {}
            for k, v in quantitative.items():
                new_key = normalize_col(k)
                updated_quantitative[new_key] = v
            quantitative.clear()
            quantitative.update(updated_quantitative)

            # Normalize the column lists as well
            char_columns = [normalize_col(col) for col in char_columns]
            pass_columns = [normalize_col(col) for col in pass_columns]
        print(f"Characterisation columns: {char_columns}")
        print(f"Passport columns: {pass_columns}")

        if not char_columns and not pass_columns:
            return None, None, None  # Skip this DB

        select_clause = []
        if char_columns:
            select_clause.extend([f"c.[{col}]" for col in char_columns])
        if pass_columns:
            select_clause.extend([f"p.[{col}]" for col in pass_columns])
        if not select_clause:
            select_clause = ["c.[ICRISAT accession identifier]", "p.[ICRISAT accession identifier]"]

        char_conditions, char_values = [], []
        pass_conditions, pass_values = [], []

        for column, val in qualitative.items():
            if column in characterisation_columns:
                char_conditions.append(f"c.[{column}] = ?")
                char_values.append(val)
            elif column in passport_columns:
                pass_conditions.append(f"p.[{column}] = ?")
                pass_values.append(val)

        for column, info in quantitative.items():
            try:
                condition_str, vals = build_condition(column, info["operator"], info["value"])
                if column in characterisation_columns:
                    char_conditions.append(f"c.{condition_str}")
                    char_values.extend(vals)
                elif column in passport_columns:
                    pass_conditions.append(f"p.{condition_str}")
                    pass_values.extend(vals)
            except Exception as e:
                return None, None, None  # On error, skip

        final_values = char_values + pass_values
        where_clause = ""
        if char_conditions or pass_conditions:
            all_conditions = char_conditions + pass_conditions
            where_clause = "WHERE " + " AND ".join(all_conditions)

        query = f"""
            SELECT {", ".join(select_clause)}
            FROM [dbo].[Characterization] c
            JOIN [dbo].[Passport] p
            ON c.[ICRISAT accession identifier] = p.[ICRISAT accession identifier]
            {where_clause}
        """
        return query, final_values, conn_func

    # Run for Sorghum
    query_s, values_s, conn_func_s = build_query(
        characterisation_columns_sorghum,
        passport_columns_sorghum,
        get_connection_sorghum
    )
    if(query_s and values_s and conn_func_s):
        results_s = run_query_for_db(query_s, values_s, conn_func_s) if query_s else []

    # Run for Chickpea
    query_c, values_c, conn_func_c = build_query(
        characterisation_columns_chickpea,
        passport_columns_chickpea,
        get_connection_chickpea
    )
    if(query_c and values_c and conn_func_c):
        results_c = run_query_for_db(query_c, values_c, conn_func_c) if query_c else []

    final_results = (results_s or []) + (results_c or [])

    if not final_results:
        return "No results found"
    return final_results

    
    # Create select statement for specific columns
    # select_clause = []
    # if char_columns:
    #     select_clause.extend([f"c.[{col}]" for col in char_columns])
    # if pass_columns:
    #     select_clause.extend([f"p.[{col}]" for col in pass_columns])
    
    # select_statement = ", ".join(select_clause)
    
    # # If no specific columns were requested, default to ID column
    # if not select_statement:
    #     select_statement = "c.[ICRISAT accession identifier], p.[ICRISAT accession identifier]"

    # char_conditions = []
    # char_values = []
    # pass_conditions = []
    # pass_values = []

    # for column, val in qualitative.items():
    #     if column in characterisation_columns:
    #         char_conditions.append(f"c.[{column}] = ?")
    #         char_values.append(val)
    #     elif column in passport_columns:
    #         pass_conditions.append(f"p.[{column}] = ?")
    #         pass_values.append(val)

    # for column, info in quantitative.items():
    #     try:
    #         condition_str, vals = build_condition(column, info["operator"], info["value"])
    #         if column in characterisation_columns:
    #             char_conditions.append(f"c.{condition_str}")
    #             char_values.extend(vals)
    #         elif column in passport_columns:
    #             pass_conditions.append(f"p.{condition_str}")
    #             pass_values.extend(vals)
    #     except Exception as e:
    #         return jsonify({"error": str(e)}), 400

    # where_clause = ""
    # final_values = []

    # if char_conditions or pass_conditions:
    #     where_clause = "WHERE "
    #     all_conditions = []

    #     if char_conditions:
    #         all_conditions.extend(char_conditions)
    #         final_values.extend(char_values)

    #     if pass_conditions:
    #         all_conditions.extend(pass_conditions)
    #         final_values.extend(pass_values)

    #     where_clause += " AND ".join(all_conditions)

    # query = f"""
    #     SELECT {select_statement}
    #     FROM [dbo].[Characterization] c
    #     JOIN [dbo].[Passport] p
    #     ON c.[ICRISAT accession identifier] = p.[ICRISAT accession identifier]
    #     {where_clause}
    # """
    # try:
    #     conn = get_connection()
    #     cursor = conn.cursor()
    #     cursor.execute(query, tuple(final_values))
    #     rows = cursor.fetchall()
    #     columns = [column[0] for column in cursor.description]
    #     results = [dict(zip(columns, row)) for row in rows]
    #     return results if results else "No results found"
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500
    # finally:
    #     conn.close()





@app.route('/search', methods=['POST'])
def search():
    query = request.json.get("query", "")
    results = get_final_results(query)

    return jsonify({"results":results if results else "No results found"})


if __name__ == "__main__":
    app.run(debug=True)
