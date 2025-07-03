# This file verifies whether the ID extracted exists in given input transaction records
# It also verifies for duplicate transaction ID
# The input file is the PDF file to be sent by the teacher
import pandas as pd
import pdfplumber
from pathlib import Path

# File locations:
transactionReportPath = "TransactionReport.pdf"
extractedDataPath = "processed_transactions.csv"
outputPath = "verified_transactions.csv"
verifiedDBPath = "verified_ID.csv"
# ---


def inputReport():
    """Processes the report into an array like object containing all RRN numbers"""
    rrnXRange = None
    rrnList = []
    with pdfplumber.open(transactionReportPath) as pdf:
        for page in pdf.pages:
            words = page.extract_words(  # Tweaked some settings so that words do not clump together
                keep_blank_chars=False,
                use_text_flow=True,
                x_tolerance=1,  # more precise word detection
                y_tolerance=1.0,
            )
            # Find x-position of "rrn"
            if rrnXRange is None:
                for w in words:
                    if w["text"].lower().strip() == "rrn":
                        x0 = w["x0"]
                        rrnXRange = (x0 - 2, x0 + 2)  # add a small margin
                        break
            # Find all words that fall within this x-range (column)
            if rrnXRange:
                for w in words:
                    if rrnXRange[0] <= w["x0"] <= rrnXRange[1]:
                        if w["text"].isdigit() and len(w["text"]) >= 10:
                            rrnList.append(w["text"])

    # Final result
    df = pd.DataFrame(rrnList, columns=["rrn"])
    df[~df.isna()] = df[~df.isna()].astype(int)
    return df


def reportVerification(inputDF, reportDF):
    """Verifies the extracted transaction IDs with the RRN in report"""
    # Adding verified/not verified
    inputDF["Verification"] = inputDF["extracted_transaction_id"].apply(
        lambda rrn: "Verified"
        if rrn in set(reportDF.dropna()["rrn"].astype(int))
        else "Not Verified"
    )

    # Adding ID not found
    inputDF.loc[inputDF["extracted_transaction_id"].isna(), "Verification"] = (
        "No ID extracted"
    )

    return inputDF


def duplicateCheck(inputDF):
    verifiedFile = Path(verifiedDBPath)
    # Check if file exists. Make new if not
    if verifiedFile.exists():
        dfVerified = pd.read_csv(verifiedFile, dtype={"rrn": int})
    else:
        dfVerified = pd.DataFrame(columns=["rrn"])

    # Checking for duplicates
    inputDF["extracted_transaction_id"] = (
        inputDF["extracted_transaction_id"].dropna().astype(int)
    )
    inputDF["duplicate"] = inputDF["extracted_transaction_id"].apply(
        lambda rrn: rrn in set(dfVerified["rrn"].astype(int))
    )

    # Adding the non duplicate rnn to the verified database
    nonDuplicateVerified = inputDF.loc[
        ((inputDF["Verification"] == "Verified") & (~inputDF["duplicate"])),
        "extracted_transaction_id",
    ]
    if not nonDuplicateVerified.empty:
        dfVerified = pd.DataFrame(
            {
                "rrn": pd.concat(
                    [dfVerified["rrn"], nonDuplicateVerified],
                    ignore_index=True,
                ).drop_duplicates()
            }
        )
        dfVerified.to_csv(verifiedFile, index=False)

    # Changing the "Verified" status of duplicates
    inputDF.loc[inputDF["duplicate"], "Verification"] = "Duplicate"
    inputDF.drop(columns=["duplicate"], inplace=True)

    return inputDF


def save(outputDf: pd.DataFrame):
    outputDf.to_csv(outputPath, index=False)


def main():
    # Input
    rrnInput = inputReport()
    extractedInput = pd.read_csv(
        extractedDataPath, dtype={"extracted_transaction_id": "Int64"}
    )

    # Process
    df = reportVerification(extractedInput, rrnInput)
    df = duplicateCheck(df)

    # Output
    save(df)


if __name__ == "__main__":
    main()
