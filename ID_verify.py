# This file verifies whether the ID extracted exists in given input transaction records
# It also verifies for duplicate transaction ID
# The input file is the PDF file to be sent by the teacher
import pandas as pd
from pathlib import Path
import os
import json
import glob

# File locations:
TRANSACTION_REPORT_PATH = "TransactionReport.pdf"
EXTRACTED_DATA_PATH = "processed_transactions.csv"  # or .xlsx
OUTPUT_PATH = "verified_transactions.csv"  # or .xlsx
VERIFIED_DB_PATH = "verified_ID.csv"  # or .xlsx
# ---


def load_column_config():
    """Load column configuration from JSON file"""
    try:
        if os.path.exists("column_config.json"):
            with open("column_config.json", "r") as f:
                config = json.load(f)
                return config.get("rrn_column", "rrn"), config.get("amount_column", "amount")
    except:
        pass
    return "rrn", "amount"

def input_report():
    """Processes all transaction report files and combines them into a single dataframe"""
    all_dfs = []
    
    # Check for single files
    single_files = [
        ("TransactionReport.xlsx", "xlsx"), 
        ("TransactionReport.csv", "csv")
    ]
    
    # Check for numbered files
    numbered_files = []
    for ext in ["xlsx", "csv"]:
        numbered_files.extend([(f, ext) for f in glob.glob(f"TransactionReport_*.{ext}")])
    
    # Combine all found files
    found_files = [(f, ext) for f, ext in single_files if os.path.exists(f)]
    found_files.extend(numbered_files)
    
    if not found_files:
        raise FileNotFoundError("No transaction report files found (CSV or Excel)")
    
    print(f"Processing {len(found_files)} transaction report file(s)...")
    
    for file_path, file_type in found_files:
        print(f"Processing: {file_path}")
        
        if file_type == "xlsx":
            df = process_excel_report(file_path)
        elif file_type == "csv":
            df = process_csv_report(file_path)
        
        if not df.empty:
            all_dfs.append(df)
    
    if not all_dfs:
        raise ValueError("No valid data found in transaction report files")
    
    # Combine all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Remove duplicates based on RRN
    combined_df = combined_df.drop_duplicates(subset=['rrn'])
    
    print(f"Total unique transactions loaded: {len(combined_df)}")
    return combined_df

def process_excel_report(excel_path):
    """Processes Excel transaction report with custom column names"""
    df = pd.read_excel(excel_path)
    rrn_col, amount_col = load_column_config()
    
    # Check if specified columns exist
    if rrn_col not in df.columns:
        raise ValueError(f"Column '{rrn_col}' not found in {excel_path}. Available columns: {list(df.columns)}")
    if amount_col not in df.columns:
        raise ValueError(f"Column '{amount_col}' not found in {excel_path}. Available columns: {list(df.columns)}")
    
    # Rename columns to standard names
    df_processed = df[[rrn_col, amount_col]].copy()
    df_processed.columns = ['rrn', 'amount']
    
    # Convert data types
    df_processed["rrn"] = df_processed["rrn"].astype("Int64")
    df_processed["amount"] = df_processed["amount"].astype("Int32")
    
    return df_processed

def process_csv_report(csv_path):
    """Processes CSV transaction report with custom column names"""
    df = pd.read_csv(csv_path)
    rrn_col, amount_col = load_column_config()
    
    # Check if specified columns exist
    if rrn_col not in df.columns:
        raise ValueError(f"Column '{rrn_col}' not found in {csv_path}. Available columns: {list(df.columns)}")
    if amount_col not in df.columns:
        raise ValueError(f"Column '{amount_col}' not found in {csv_path}. Available columns: {list(df.columns)}")
    
    # Rename columns to standard names
    df_processed = df[[rrn_col, amount_col]].copy()
    df_processed.columns = ['rrn', 'amount']
    
    # Convert data types
    df_processed["rrn"] = df_processed["rrn"].astype("Int64")
    df_processed["amount"] = df_processed["amount"].astype("Int32")
    
    return df_processed


def id_verification(input_df, report_df):
    """Verifies the extracted transaction IDs with the ones in report"""
    # Adding verified/not verified
    input_df["Verification"] = input_df["extracted_transaction_id"].apply(
        lambda rrn: (
            "Verified"
            if rrn in set(report_df.dropna()["rrn"].astype(int))
            else "Not Verified"
        )
    )

    # Adding ID not found
    input_df.loc[input_df["extracted_transaction_id"].isna(), "Verification"] = (
        "No ID extracted"
    )

    return input_df


def read_verified_file():
    """Reads and returns the dataframe of Verified ID (csv or xlsx)"""
    verified_file = Path(VERIFIED_DB_PATH)
    # Check if file exists. Make new if not
    if verified_file.exists():
        if verified_file.suffix == ".xlsx":
            verified_df = pd.read_excel(verified_file, dtype={"rrn": int})
        else:
            verified_df = pd.read_csv(verified_file, dtype={"rrn": int})
    else:
        verified_df = pd.DataFrame(columns=["rrn"])
    return verified_df


def duplicate_check(input_df):
    """Checks for duplicate extracted IDs in verified IDs"""
    # Checking for duplicates
    verified_dataframe = read_verified_file()

    # Identifying duplicates
    input_df["duplicate"] = input_df["extracted_transaction_id"].apply(
        lambda rrn: rrn in set(verified_dataframe["rrn"].astype(int)) if pd.notna(rrn) else False
    )

    # Changing the "Verified" status of duplicates
    input_df.loc[input_df["duplicate"], "Verification"] = "Duplicate"
    
    # Appending the non duplicate verified entries to the verified database
    append_verified(input_df, verified_dataframe)
    
    input_df.drop(columns=["duplicate"], inplace=True)

    return input_df


def mismatch_check(input_df, report_df):
    """Checks for mismatch amount from the report"""
    
    # Skip amount mismatch check if 'amount' column doesn't exist in input_df
    # This is normal since extracted data from screenshots typically doesn't include amounts
    if 'amount' not in input_df.columns:
        print("Skipping amount mismatch check - no amount data in extracted transactions")
        return input_df
    
    # Create a lookup dictionary for report amounts for efficiency
    report_amounts = dict(zip(report_df['rrn'], report_df['amount']))
    
    def check_amount_mismatch(row):
        transaction_id = row['extracted_transaction_id']
        if pd.isna(transaction_id) or transaction_id not in report_amounts:
            return False
        
        input_amount = row.get('amount', None)
        if pd.isna(input_amount):
            return False
            
        report_amount = report_amounts[transaction_id]
        return input_amount != report_amount
    
    # Apply the mismatch check
    input_df["amtVerify"] = input_df.apply(check_amount_mismatch, axis=1)
    input_df.loc[input_df["amtVerify"], "Verification"] = "Amount mismatch"
    
    input_df.drop(columns=["amtVerify"], inplace=True)
    return input_df


def append_verified(input_df, verified_df):
    """Appends the unique verified IDs in input_df to verified_df and saves verified_df (csv or xlsx)"""
    # Get verified transactions that are NOT duplicates
    newly_verified_IDs = input_df.loc[
        (input_df["Verification"] == "Verified") & (~input_df["duplicate"]), 
        "extracted_transaction_id"
    ]
    
    if not newly_verified_IDs.empty:
        verified_df = pd.DataFrame(
            {
                "rrn": pd.concat(
                    [verified_df["rrn"], newly_verified_IDs],
                    ignore_index=True,
                ).drop_duplicates()
            }
        )
        if Path(VERIFIED_DB_PATH).suffix == ".xlsx":
            verified_df.to_excel(VERIFIED_DB_PATH, index=False)
        else:
            verified_df.to_csv(VERIFIED_DB_PATH, index=False)


def save(output_df: pd.DataFrame):
    if Path(OUTPUT_PATH).suffix == ".xlsx":
        output_df.to_excel(OUTPUT_PATH, index=False)
    else:
        output_df.to_csv(OUTPUT_PATH, index=False)


def main():
    # Input
    report_input = input_report()
    
    # Determine which extracted data file exists
    extracted_data_path = None
    if os.path.exists("processed_transactions.xlsx"):
        extracted_data_path = "processed_transactions.xlsx"
    elif os.path.exists("processed_transactions.csv"):
        extracted_data_path = "processed_transactions.csv"
    else:
        raise FileNotFoundError("No processed transactions file found (processed_transactions.csv or processed_transactions.xlsx)")
    
    # Read the extracted data file
    if extracted_data_path.endswith('.xlsx'):
        extracted_input = pd.read_excel(
            extracted_data_path,
            dtype={"extracted_transaction_id": "Int64"},
        )
    else:
        extracted_input = pd.read_csv(
            extracted_data_path,
            dtype={"extracted_transaction_id": "Int64"},
        )
    
    # Add amount column with proper dtype if it exists, otherwise skip amount verification
    if 'amount' in extracted_input.columns:
        extracted_input['amount'] = extracted_input['amount'].astype("Int32")
    else:
        print("No amount column found in extracted data - amount verification will be skipped")

    # Process
    # Order: ID verification > duplicates (append non duplicates) > amount mismatch
    # Example: if a transaction is marked duplicate it would not be checked for amount mismatch etc.
    df = id_verification(extracted_input, report_input)
    df = duplicate_check(df)
    df = mismatch_check(df, report_input)

    # Output
    save(df)


if __name__ == "__main__":
    main()
