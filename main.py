import boto3
import re
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
import json

receipts_folder = Path('test')
image_extensions = ['.png', '.jpg', '.jpeg']
textract = boto3.client('textract', region_name='ap-southeast-2') #Sydney region
output_file = "receipts_output.xlsx"
results = []

#Function to write the extracted data to Excel file
def write_to_file(data, output_file):
    wb = Workbook()
    ws = wb.active
    ws.title = "Receipts"
    ws.append(["Filename", "Company Name", "Date", "Amount"])
    for row in data:
        ws.append(row)
    wb.save(output_file)
    print(f"Data written to {output_file}")

#Placeholder function for extracting company name
def extract_company_name(lines):
    known_companies = ['Woolworths', 'Mitre 10', 'Officeworks', 'JB Hi-Fi', 'Bunnings', 'Kmart', 'BP', 'BP Connect', 'Spicer']
    #Check for keywords in the first few lines of the receipt
    for line in lines:
        if any(keyword in line for keyword in ["Company", "Inc.", "LLC", "Ltd"]):
            return line.strip()
    
    #If no company found from keywords, check against known companies
    for line in lines:
        for known_company in known_companies:
            if known_company.lower() in line.lower():
                return known_company
    
    #Last resort: Assume the first line is the company name
    return lines[0].strip() if lines else ""

def extract_date(lines):
    #Initialise regex expression for date and time patterns
    date_patterns = [
        r'(\d{2}[/-]\d{2}[/-]\d{4})', #12-07-2025 or 12/07/2025
        r'(\d{4}[/-]\d{2}[/-]\d{2})', #2025-07-12 or 2025/07/12
        r'(\d{1,2} [A-Za-z]{3,9} \d{4})', #12 JULY 2025
        r'(\d{1,2}[A-Za-z]{3}\d{4})',  #12JUL2025
    ]
    time_patterns = [
        r'(\d{1,2}[:.]\d{2}\s?(?:a\.?m\.?|p\.?m\.?|AM|PM))', #8:53 am, 12:05 PM, 8.53a.m., 12.05P.M.
        r'(\d{1,2}:\d{2})', #14:30
        r'(\d{1,2}:\d{2}:\d{2})' #14:30:15
    ]
    found_date = None
    found_time = None

    for line in lines:
        #Find date
        if not found_date:
            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    found_date = match.group(1)
                    break
        #Find time
        if not found_time:
            for tpattern in time_patterns:
                tmatch = re.search(tpattern, line, re.IGNORECASE)
                if tmatch:
                    found_time = tmatch.group(1)
                    break
        #If both date and time found, exit loop
        if found_date and found_time:
            break

    if found_date:       
        # Parse date format
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d %B %Y", "%d %b %Y", "%d%b%Y"]:
            try:
                dt = datetime.strptime(found_date, fmt)
                # Format as DD-MM-YYYY:HH:mm
                # If time is in HH:mm:ss, take only HH:mm
                if len(found_time) > 5:
                    found_time = found_time[:5]
                print(f"Parsed date: {dt.strftime('%d-%m-%Y')} Time: {found_time}")
                return dt.strftime("%d-%m-%Y") + ":" + found_time
            except ValueError:
                continue
    return ""

def extract_amount(lines):
    # List of Keywords to look for in lines that likely contain the total amount
    keywords = ['total', 'total incl gst', 'total amount', 'amount due', 'grand total', 'balance due']
    amount_pattern = r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})' #ex: $1,234.56 or 1234.56
    keyword_amounts = []
    all_amounts = []

    for line in lines:
        matches = re.findall(amount_pattern, line)
        for amt in matches:
            all_amounts.append(amt)
        # Check for keywords in line (case-insensitive)
        if any(k in line.lower() for k in keywords):
            for amt in matches:
                keyword_amounts.append(amt)

    # Prefer amounts found in keyword lines
    amounts = keyword_amounts if keyword_amounts else all_amounts
    if amounts:
        cleaned = []
        for amt in amounts:
            val = float(amt.replace('$','').replace(',',''))
            if val not in cleaned:
                cleaned.append(val)
     
        max_index = cleaned.index(max(cleaned))
        return cleaned[max_index]
    return ""

def extract_text_from_image(image_path):
    with open(image_path, 'rb') as document:
        image_bytes = document.read()

    response = textract.detect_document_text(Document={'Bytes': image_bytes})
    lines = [item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE']

    company = extract_company_name(lines)
    date = extract_date(lines)
    amount = extract_amount(lines)
    filename = Path(image_path).name
    results.append([filename, company, date, amount])
    write_to_file(results, output_file)

#Main function to test the extractor
def main():
    for image_file in receipts_folder.iterdir():
        if image_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            print(f'Processing {image_file.name}')
            extract_text_from_image(str(image_file))


if __name__ == '__main__':
    main()