# Import necessary libraries for handling files, making HTTP requests, parsing HTML content, working with data, and generating PDFs.
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Path to the Excel file
excel_file = 'codes.xlsx'  # Update this path to your Excel file

# Directory to store PDFs
pdf_dir = 'downloaded_pdfs'
os.makedirs(pdf_dir, exist_ok=True)

# Define headers to simulate a browser visit. This helps in avoiding being blocked by websites that check for bots.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Define a function that fetches content from a URL and converts it to a PDF file.
def url_to_pdf(url):
    try:
        # Make an HTTP GET request to the URL using the defined headers.
        response = requests.get(url, headers=headers)

        # Raise an HTTPError exception for 4xx/5xx responses.
        response.raise_for_status()  
        
        
        # Parse the HTML content of the page using BeautifulSoup.
        soup = BeautifulSoup(response.text, 'html.parser')

        # Attempt to find the first <h2> tag to use its text as the filename.
        h2_tag = soup.find('h2')
        if h2_tag:
            # Replace spaces with underscores in the <h2> text to form the base filename.
            base_name = h2_tag.text.strip().replace(' ', '_')
        else:
            # Use a generic base name if no <h2> tag is found.
            base_name = 'document'
        
        # Remove any characters that are not alphanumeric or underscores
        safe_name = ''.join(char if char.isalnum() or char == '_' else '' for char in base_name)[:50]  # Limit to 50 chars
        file_name = f"{safe_name}.pdf"
        file_path = os.path.join(pdf_dir, file_name)

        # Create a PDF with the extracted text
        c = canvas.Canvas(file_path, pagesize=letter)
        text_obj = c.beginText(40, 740)  # Start near the top-left of the page
        text_obj.setFont("Helvetica", 10)
        text = soup.get_text()

        # Add the extracted text to the PDF, line by line.
        for line in text.split('\n'):
            if line.strip():
                text_obj.textLine(line.strip())

        # Draw the text object on the canvas and save the PDF.
        c.drawText(text_obj)
        c.save()
        print(f'Successfully created PDF: {file_path}')

    except Exception as e:
        print(f'Error processing {url}: {e}')

# Read URLs from the Excel file into a DataFrame. Assumes URLs are in the first column.
df = pd.read_excel(excel_file, header=None)  

# Iterate over each URL in the DataFrame, converting it to a PDF.
for url in df[0].dropna():  # Iterates over each URL in the first column, ignoring NaN values
    url_to_pdf(url)
