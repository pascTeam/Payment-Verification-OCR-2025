# This file verifies whether the ID extracted are duplicate or not.
# The input file is the PDF file to be sent by the teacher
import pandas as pd
import pdfplumber

# File locations:
transactionReportPath = "TransactionReport.pdf"
extractedDataPath = "processed_transactions.csv"
outputPath = "verified_transactions.csv"
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
                # word_margin=0.1,  # helps separate adjacent words
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
    return df


def save(outputDf: pd.DataFrame):
    outputDf.to_csv(outputPath, index=False)


def main():
    rrnInput = inputReport()
    extractedInput = pd.read_csv(extractedDataPath)

    # Adding verified/not verified
    extractedInput["Verification"] = extractedInput["extracted_transaction_id"].apply(
        lambda rrn: "Verified"
        if rrn in set(rrnInput.dropna()["rrn"])
        else "Not Verified"
    )

    # Adding ID not found
    extractedInput.loc[
        extractedInput["extracted_transaction_id"].isna(), "Verification"
    ] = "No ID extracted"

    save(extractedInput)


if __name__ == "__main__":
    main()
