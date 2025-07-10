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
MODEL_PATH = "model.pt"
INPUT_PATH = "input.csv"
# Input format:
# column : "screenshots" with all screenshot URLs
OUTPUT_PATH = "processed_transactions.csv"
# ---

model = YOLO(MODEL_PATH)

# Functions


def find_id_box(img):
    """
    Runs the YOLO model on the input image and returns detected boxes or None.

    Args:
        img (np.ndarray): The input image as a NumPy array.

    Returns:
        boxes (ultralytics.yolo.engine.results.Boxes or None): Detected bounding boxes, or None if no boxes are found or an error occurs.
    """
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
    """
    Crops the input image to the first detected YOLO bounding box.

    Args:
        img (np.ndarray): The input image as a NumPy array.

    Returns:
        cropped_img (np.ndarray or None): Cropped image as a NumPy array, or None if no box is found.
    """
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
    """
    Downloads an image from a given URL and returns it as a NumPy array.

    Args:
        image_url (str): URL of the image to download.

    Returns:
        img (np.ndarray or None): Decoded image as a NumPy array, or None if download fails.
    """
    response = requests.get(image_url)
    if response.status_code == 200:
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return None


def process_image_url(image_url):
    """
    Processes an image URL: downloads, crops, runs OCR, and extracts the transaction ID.

    Args:
        image_url (str): URL of the image to process.

    Returns:
        transaction_id (str or None): Extracted transaction ID, or None if extraction fails.
    """
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
            print(extract)
            return extract
        return None
    except Exception as e:
        print(
            f"[ERROR] Failed to process image URL: {image_url}\nException: {e}")
        return None


def extract_transaction_details(text):
    """
    Extracts a 12-digit transaction ID from OCR text.

    Args:
        text (str): OCR-extracted text from the transaction screenshot.

    Returns:
        transaction_id (str or None): 12-digit transaction ID if found, else None.
    """
    lines = text.split("\n")
    transaction_id = None
    print(lines)
    if (len(lines) == 2):
        transaction_id = lines[0][-12:]
    elif (len(lines) == 3):
        transaction_id = lines[1]
    pattern = r'^\d{12}$'
    if re.match(pattern, transaction_id):
        return transaction_id
    else:
        return None


def process_transactions(reg_path):
    """
    Processes an input CSV file to extract transaction IDs from screenshots.

    Args:
        reg_path (str): Path to the input CSV file.

    Returns:
        reg (pd.DataFrame): DataFrame with an added 'extracted_transaction_id' column.
    """
    reg = pd.read_csv(reg_path, dtype=str)
    reg["extracted_transaction_id"] = (
        reg["screenshot"].dropna().apply(process_image_url)
    )
    return reg


def save(df, output_filename="processed_transactions.xlsx"):
    """
    Saves the processed DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame to save.
        output_filename (str): Output CSV filename.
    """
    df["extracted_transaction_id"] = df["extracted_transaction_id"].astype(
        "Int64")
    df.to_csv(output_filename, index=False)
    # files.download(output_filename)


def main():
    """
    Main function to handle input, processing, and output.
    """
    processed_df = process_transactions(INPUT_PATH)
    save(processed_df, OUTPUT_PATH)


if __name__ == "__main__":
    main()
