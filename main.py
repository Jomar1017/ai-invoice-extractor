from pathlib import Path
from PIL import Image
import boto3

receipts_folder = Path('test')
image_extensions = ['.png', '.jpg', '.jpeg']
textract = boto3.client('textract', region_name='ap-southeast-2') #Sydney region


#Iterate through images in a folder and print their details
def iterate_images(folder_path):
    folder = Path(folder_path)
    for image_file in folder.iterdir():
        if image_file.suffix.lower() in image_extensions:
            try:
                with Image.open(image_file) as img:
                    print(f"Read image: {image_file.name}, size: {img.size}, format: {img.format}")
            except Exception as e:
                print(f"Failed to open {image_file.name}: {e}")

def extract_text_from_image(image_path):
    client = boto3.client('textract')
    with open(image_path, 'rb') as document:
        image_bytes = document.read()
    response = client.detect_document_text(Document={'Bytes': image_bytes})
    lines = [item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE']
    return lines

# Main function to test the image iteration
def main():
    test_folder = Path('test')
    for image_file in test_folder.iterdir():
        if image_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            print(f'Processing {image_file.name}')
            lines = extract_text_from_image(str(image_file))
            print('\n'.join(lines))
            # TODO: Add logic to extract Company, Date, Amount, Invoice Number from lines

if __name__ == '__main__':
    main()