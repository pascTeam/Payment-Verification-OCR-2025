# Imports
import cv2
import numpy as np
import re
import pytesseract
import requests
import pandas as pd
from ultralytics import YOLO

# --- IMP: Set the paths of the following properly
# Include the code to choose yolo model here
modelPath = "model.pt"
inputPath = "sample.csv"
# Input format:
# column : "screenshots" with all screenshot URLs
outputPath = "processed_transactions.csv"
# ---

model = YOLO(modelPath)
# Functions


def find_id_box(img):
    """Run YOLOv12 model on image and return detected boxes or None."""
    try:
        results = model.predict(img)
        boxes = results[0].boxes  # boxes object
        if boxes is None or len(boxes) == 0:
            return None
        return boxes
    except Exception as e:
        print(f"Error while running model on image\nException: {e}")
        return None


def crop_image(img):
    """Crop image to first detected YOLO box or return None."""
    boxes = find_id_box(img)
    if boxes is None:
        return None

    # Use the first detected box
    box = boxes.xyxy[0]  # (x1, y1, x2, y2)

    x1, y1, x2, y2 = map(int, box)

    # Crop the image
    cropped_img = img[y1:y2, x1:x2]
    return cropped_img


def download_image(image_url):
    """Downloads an image from a given URL and returns it as a NumPy array."""
    response = requests.get(image_url)
    if response.status_code == 200:
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return None


def process_image_url(image_url):
    """Processes an image URL and returns the extracted transaction ID."""
    try:
        if not image_url:
            return None
        image = download_image(image_url)
        if image is not None:
            cropped = crop_image(image)
            if cropped is None:
                return None
            text = pytesseract.image_to_string(cropped)
            extract = extract_transaction_details(text)
            return extract
        return None
    except Exception as e:
        print(f"[ERROR] Failed to process image URL: {image_url}\nException: {e}")
        return None


def extract_transaction_details(text):
    """Extracts UTR Number (PhonePe), UPI Transaction ID (Google Pay), or Paytm Transaction ID from text."""
    lines = text.split("\n")
    buffer = ""

    for i, line in enumerate(lines):
        # Combine previous buffer if present (handles label on one line, ID on next)
        combined = buffer + " " + line if buffer else line

        # Match UPI transaction ID / UTR from current or buffered+current line
        match_upi = re.search(
            r"(?:UPI Ref(?:erence)?|UTR|Ref(?:erence)? ID|UPI transaction ID)[:\s]*([A-Za-z0-9]{9,})",
            combined,
            re.IGNORECASE,
        )

        if match_upi:
            return match_upi.group(1)

        # Buffer this line if it might be a label but doesn't contain the ID
        if re.search(
            r"(UPI Ref(?:erence)?|UTR|Ref(?:erence)? ID|UPI transaction ID|Bank Reference Id)",
            line,
            re.IGNORECASE,
        ):
            buffer = line
        else:
            buffer = ""

    return None  # No transaction ID found


def process_transactions(reg_path):
    """Processes an input file to extract and verify transaction details."""
    reg = pd.read_csv(reg_path, dtype=str)
    reg["extracted_transaction_id"] = (
        reg["screenshot"].dropna().apply(process_image_url)
    )
    return reg


def save(df, output_filename="processed_transactions.xlsx"):
    """Saves the processed dataframe"""
    df.to_csv(output_filename, index=False)
    # files.download(output_filename)


def main():
    """Main function to handle input, processing, and output."""
    processed_df = process_transactions(inputPath)
    save(processed_df, outputPath)


if __name__ == "__main__":
    main()
