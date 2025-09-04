# AI Receipt Data Extractor
Extracts details from receipt images such as the Company name, Date, and Amount using AWS Textract and Python.
Outputs the structured data into Excel file.


## Features
- Detects text from local invoice images
- Extracts Company name, date, and amount
- Saves extracted data to Excel

## Usage
1. Place receipt images in test folder
2. Configure AWS credentials ('aws configure') - Make sure AWS credentials has AWSTextractFullPolicy configured
3. Run main.py
4. Check the 'Invoices.xlsx' file