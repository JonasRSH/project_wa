from PyPDF2 import PdfReader
import pandas as pd

# Path to the PDF file
input_file = '/Users/Jonas_1/Documents/Jonas/Informatik/Projekt_WA/Python_Back_End/t1_reader/MRN 25CH02GBIXU8MM7NJ0.pdf'

# Open the PDF file
try:
    reader = PdfReader(input_file)
    for page in reader.pages:
        text = page.extract_text()
        print(text)
except FileNotFoundError:
    print(f"Error: The file {input_file} does not exist.")
    exit(1)

# Extract text from the PDF
text = ""
for page_num in range(len(reader.pages)):
    page = reader.pages[page_num]
    text += page.extract_text() or ""

# Process the extracted text to find the required columns
# This is a simple example and may need to be adjusted based on the actual PDF content
lines = text.split('\n')
data = []
required_columns = ['MRN', 'Packst. insgesamt', 'Warenbezeichnung', 'Gesamte Rohmasse']
for line in lines:
    if any(col in line for col in required_columns):
        data.append(line.split())

# Convert the data to a DataFrame
df = pd.DataFrame(data, columns=required_columns)


# Print the DataFrame (for verification)
print(df)