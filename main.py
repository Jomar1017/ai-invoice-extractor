import boto3
import re
from datetime import datetime
from pathlib import Path

receipts_folder = Path('test2')
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

def extract_date(lines):
    #Initialise regex expression for date and time patterns
    date_patterns = [
        r'(\d{2}[/-]\d{2}[/-]\d{4})', #12-07-2025 or 12/07/2025
        r'(\d{4}[/-]\d{2}[/-]\d{2})', #2025-07-12 or 2025/07/12
        r'(\d{2} [A-Za-z]{3,9} \d{4})', #12 JULY 2025
        r'(\d{2}[A-Za-z]{3}\d{4})',  #12JUL2025
    ]
    time_patterns = [r'(\d{2}:\d{2})', r'(\d{2}:\d{2}:\d{2})']
    found_date = None
    found_time = "00:00"

    for line in lines:
        #Find date
        for pattern in date_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                found_date = match.group(1)
                #print(f"Found date: {found_date}")
                break
        #Find time
        for tpattern in time_patterns:
            tmatch = re.search(tpattern, line)
            if tmatch:
                found_time = tmatch.group(1)
                #print(f"Found time: {found_time}")
                break
        if found_date:
            break

    if found_date:       
        # Try parsing date
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d %B %Y", "%d %b %Y", "%d%b%Y"]:
            try:
                dt = datetime.strptime(found_date, fmt)
                # Format as DD-MM-YYYY:HH:mm
                # If time is in HH:mm:ss, take only HH:mm
                if len(found_time) == 8:
                    found_time = found_time[:5]
                return dt.strftime("%d-%m-%Y") + ":" + found_time
            except ValueError:
                continue
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