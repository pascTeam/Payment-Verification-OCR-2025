# This file verifies whether the ID extracted exists in given input transaction records
# It also verifies for duplicate transaction ID
# The input file is the PDF file to be sent by the teacher
import pandas as pd
import pdfplumber
from pathlib import Path

# File locations:
TRANSACTION_REPORT_PATH = "TransactionReport.pdf"
EXTRACTED_DATA_PATH = "processed_transactions.csv"
OUTPUT_PATH = "verified_transactions.csv"
VERIFIED_DB_PATH = "verified_ID.csv"
# ---


def input_report():
    """Processes the report into an dataframe object containing all RRN numbers with their paid amount"""
    rrn_x_range = None
    amount_x_range = None
    rrn_list = []
    amount_list = []
    with pdfplumber.open(TRANSACTION_REPORT_PATH) as pdf:
        for page in pdf.pages:
            words = page.extract_words(  # Tweaked some settings so that words do not clump together
                keep_blank_chars=False,
                use_text_flow=True,
                x_tolerance=1,  # more precise word detection
                y_tolerance=1.0,
            )

            # Find x-position of "rrn" (x0) and "amount(rs.)" (x1)
            # we are finding x0 of rrn and x1 of amount
            # This is because in the pdf rrn column is aligned left and amount is alight right
            for w in words:
                if rrn_x_range and amount_x_range:
                    break
                if rrn_x_range is None and w["text"].lower().strip() == "rrn":
                    x0 = w["x0"]
                    rrn_x_range = (x0 - 2, x0 + 2)  # add a small margin
                elif (
                    amount_x_range is None
                    and w["text"].lower().strip() == "amount(rs.)"
                ):
                    x1 = w["x1"]
                    amount_x_range = (x1 - 5, x1 + 5)  # add a small margin
                    print(amount_x_range)

            # Find all words that fall within this x-range (column)
            if rrn_x_range:
                for w in words:
                    if rrn_x_range[0] <= w["x0"] <= rrn_x_range[1]:
                        if w["text"].isdigit() and len(w["text"]) >= 10:
                            rrn_list.append(w["text"])

            # Find all "amount" items that fall within this x-range (column)
            if amount_x_range:
                for w in words:
                    if amount_x_range[0] <= w["x1"] <= amount_x_range[1]:
                        if w["text"].isdigit():
                            amount_list.append(w["text"])

    # Final result
    df = pd.DataFrame(
        {"rrn": rrn_list, "amount": amount_list},
    )
    df["rrn"] = df["rrn"].astype("Int64")
    df["amount"] = df["amount"].astype("Int32")
    return df


def id_verification(input_df, report_df):
    """Verifies the extracted transaction IDs with the ones in report"""
    # Adding verified/not verified
    input_df["Verification"] = input_df["extracted_transaction_id"].apply(
        lambda rrn: "Verified"
        if rrn in set(report_df.dropna()["rrn"].astype(int))
        else "Not Verified"
    )

    # Adding ID not found
    input_df.loc[input_df["extracted_transaction_id"].isna(), "Verification"] = (
        "No ID extracted"
    )

    return input_df


def read_verified_file():
    """Reads and returns the dataframe of Verified ID"""
    verified_file = Path(VERIFIED_DB_PATH)
    # Check if file exists. Make new if not
    if verified_file.exists():
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
        lambda rrn: rrn in set(verified_dataframe["rrn"].astype(int))
    )

    # Appending the non duplicate entries to the verified database
    append_verified(input_df, verified_dataframe)

    # Changing the "Verified" status of duplicates
    input_df.loc[input_df["duplicate"], "Verification"] = "Duplicate"
    input_df.drop(columns=["duplicate"], inplace=True)

    return input_df


def mismatch_check(input_df, report_df):
    """Checks for mismatch amount from the report"""

    # Identifying Mismatch amount
    input_df["amtVerify"] = input_df["extracted_transaction_id"].apply(
        lambda transaction_id: input_df.loc[transaction_id, "amount"]
        != report_df.loc[transaction_id, "amount"]
    )
    input_df.loc[input_df["amtVerify"], "Verification"] = "Amount mismatch"

    input_df.drop(columns=["amtVerify"], inplace=True)
    return input_df


def append_verified(input_df, verified_df):
    """Appends the unique verified IDs in input_df to verified_df and saves verified_df"""
    # Extracting a series of unique verified IDs
    unique_verified_IDs = input_df.loc[
        input_df["duplicate"], "extracted_transaction_id"
    ]

    # Adding unique rnn to the verified database if there are any
    if not unique_verified_IDs.empty:
        verified_df = pd.DataFrame(
            {
                "rrn": pd.concat(
                    [verified_df["rrn"], unique_verified_IDs],
                    ignore_index=True,
                ).drop_duplicates()
            }
        )
        verified_df.to_csv(VERIFIED_DB_PATH, index=False)


def save(output_df: pd.DataFrame):
    output_df.to_csv(OUTPUT_PATH, index=False)


def main():
    # Input
    report_input = input_report()
    extracted_input = pd.read_csv(
        EXTRACTED_DATA_PATH,
        dtype={"extracted_transaction_id": "Int64", "amount": "Int32"},
    )

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
