import pytesseract
import cv2
import os
import re

# Optional: Set tesseract path (only needed for Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Folder containing generated Aadhaar images
image_folder = "/content/aadhaar_images_from_dataset"

# Function to extract details using OCR
def extract_info_from_image(image_path):
    # Load image
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR
    raw_text = pytesseract.image_to_string(gray)

    # Extract details using regex
    name = re.search(r'Name:\s*(.*)', raw_text)

    aadhaar = re.search(r'(?:Aadhaar\s*No[:\s]*)?(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})', raw_text, re.IGNORECASE)
    aadhaar_number = aadhaar.group(1).strip() if aadhaar else None
    dob = re.search(r'(?:DOB|D\.O\.B\.?)[:\s]*([\d]{2}[-/][\d]{2}[-/][\d]{4})', raw_text, re.IGNORECASE)
    gender = re.search(r'(?:Gender)[:\s]*(Male|Female|MALE|FEMALE)', raw_text, re.IGNORECASE)
    if not gender:
      if re.search(r'\b(MALE|Male)\b', raw_text):
        gender = re.search(r'\b(MALE|Male)\b', raw_text)
      elif re.search(r'\b(FEMALE|Female)\b', raw_text):
        gender = re.search(r'\b(FEMALE|Female)\b', raw_text)



    # Return cleaned data
    return {
        "Name": name.group(1).strip() if name else None,
        "DOB": dob.group(1).strip() if dob else None,
        "Gender": gender.group(1).strip() if gender else None,
        "Aadhaar No": aadhaar.group(1).strip() if aadhaar else None,
    }

# Iterate over all images
all_results = []
for img_file in os.listdir(image_folder):
    if img_file.endswith(".png"):
        full_path = os.path.join(image_folder, img_file)
        data = extract_info_from_image(full_path)
        print(f"\nDetails from {img_file}:")
        print(data)
        all_results.append(data)

df = pd.DataFrame(all_results)
csv_output_path = "aadhaar_ocr_results.csv"
df.to_csv(csv_output_path, index=False)
print(f"\n✅ OCR extraction complete. Results saved to: {csv_output_path}")

