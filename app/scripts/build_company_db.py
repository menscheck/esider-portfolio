import csv
import json
import os
from typing import List, Dict, Any

def generate_alias(code: str, name: str) -> str:
    """
    Generates the alias using a short name, mapping, and the first two characters.
    Keeps the alias lowercase for consistent matching.
    """
    short_name = name

    # 去掉常見字尾
    for suffix in ["股份有限公司", "有限公司", "控股", "集團"]:
        short_name = short_name.replace(suffix, "")

    # 特別映射（重點公司）
    mapping = {
        "臺灣積體電路製造": "台積電 tsmc 台積",
        "鴻海精密工業": "鴻海 foxconn",
        "宏碁": "宏碁 acer",
        "聯發科技": "聯發科 mediatek",
        "台達電子": "台達電 delta"
    }

    alias = short_name.lower()

    for k, v in mapping.items():
        if k in name:
            alias += " " + v

    # 加前兩字
    if len(short_name) >= 2:
        alias += " " + short_name[:2]

    return alias.strip().lower()


def build_company_db(csv_path: str, json_path: str):
    """
    Reads company data from a CSV file, processes it, generates aliases, 
    and saves the structured list to a JSON file.
    """
    print("--- Starting Company Database Build ---")
    companies: List[Dict[str, Any]] = []

    # Define common encodings to try reading the CSV
    encodings_to_try = ["utf-8", "big5"]
    csv_file_handle = None

    for encoding in encodings_to_try:
        print(f"Attempting to read CSV using encoding: {encoding}")
        try:
            # Use 'r' mode with the specified encoding
            csv_file_handle = open(csv_path, 'r', newline='', encoding=encoding)
            reader = csv.DictReader(csv_file_handle)
            break # Success! Exit the loop

        except UnicodeDecodeError:
            print(f"Failed to decode with {encoding}. Trying next encoding...")
            continue
        except FileNotFoundError:
             print(f"Error: CSV file not found at path: {csv_path}")
             return 0, [] # Indicate failure before loop completion


    if csv_file_handle is None:
        print("❌ Could not open or read the CSV file using any supported encoding.")
        return 0, []

    try:
        # If successful reading, iterate through rows
        reader = csv.DictReader(csv_file_handle)
        for row in reader:
            try:
                code = row.get("公司代號", "").strip()
                name = row.get("公司名稱", "").strip()

                if code and name:
                    # 1. Generate alias (using the defined function)
                    alias = generate_alias(code, name)

                    companies.append({
                        "code": code,
                        "name": name,
                        "alias": alias
                    })
            except Exception as e:
                print(f"Skipping row due to processing error: {e}")


        # 2. Write data to JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Successfully processed {len(companies)} records.")
        print(f"✨ Output saved to: {json_path}")
        return len(companies), companies

    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return 0, []
    finally:
        if csv_file_handle:
            csv_file_handle.close()

# --- Main Execution Block ---
if __name__ == "__main__":
    CSV_INPUT_PATH = "app/data/company_raw.csv"
    JSON_OUTPUT_PATH = "app/data/company_list.json"

    # NOTE: We assume the directory app/data exists or will be created by the write operation.
    total_count, result_list = build_company_db(CSV_INPUT_PATH, JSON_OUTPUT_PATH)

    if total_count > 0:
        print("\n=========================================")
        print(f"Processing complete! Total companies found: {total_count}")
        print("=========================================\n")
        # Optionally print a sample of the generated data
        print("--- Sample Data ---")
        sample = result_list[:min(3, len(result_list))]
        for item in sample:
            print(f"Code: {item['code']}, Name: {item['name']}, Alias: {item['alias']}")