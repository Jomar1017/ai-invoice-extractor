from pathlib import Path
from PIL import Image
import boto3

receipts_folder = Path('test')
image_extensions = ['.png', '.jpg', '.jpeg']
textract = boto3.client('textract', region_name='ap-southeast-2') #Sydney region

#Placeholder function for extracting company name
def extract_company_name(lines):
    known_companies = ['Woolworths', 'Coles', 'Officeworks', 'JB Hi-Fi', 'Bunnings', 'Kmart', 'BP', 'Spicer']
    #Check for keywords in the first few lines of the receipt
    for line in lines:
        if any(keyword in line for keyword in ["Company", "Inc", "LLC", "Ltd", "CO"]):
            return line.strip()
    
    #If no company found from keywords, check against known companies
    for line in lines:
        for known_company in known_companies:
            if known_company.lower() in line.lower():
                return known_company
    
    #Last resort: assume the first line is the company name
    return lines[0].strip() if lines else ""

import re

def extract_date(lines):
    #Common date patterns: DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.
    date_patterns = [
        r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',
        r'\b\d{4}[/-]\d{2}[/-]\d{2}\b',
        r'\b\d{2} [A-Za-z]{3,9} \d{4}\b',
    ]
    for line in lines:
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
    return ""

def extract_amount(lines):
    #Initialise pattern for amount, ex: $90.99 or 90.99
    amount_pattern = r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})'
    amounts = []
    for line in lines:
        matches = re.findall(amount_pattern, line)
        for amt in matches:
            amounts.append(amt)
    
    #Select only the largest amount if multiple amount found
    if amounts:
        #Clean amount -  Remove $ and , for comparison
        cleaned = [float(a.replace('$','').replace(',','')) for a in amounts]
        max_index = cleaned.index(max(cleaned))
        return amounts[max_index]
    return ""

def extract_text_from_image(image_path):
    with open(image_path, 'rb') as document:
        image_bytes = document.read()
    response = textract.detect_document_text(Document={'Bytes': image_bytes})
    lines = [item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE']
    company = extract_company_name(lines)
    date = extract_date(lines)
    amount = extract_amount(lines)
    print(f"Company: {company}")
    print(f"Date: {date}")
    print(f"Amount: {amount}")
    return lines

# Main function to test the image iteration
def main():
    for image_file in receipts_folder.iterdir():
        if image_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            print(f'Processing {image_file.name}')
            extract_text_from_image(str(image_file))


if __name__ == '__main__':
    main()