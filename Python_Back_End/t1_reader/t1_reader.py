from pypdf import PdfReader
import re


# Open the PDF file
def open_pdf(pdf_path):
        try:
            reader = PdfReader(pdf_path)
            return reader, None
        except(FileNotFoundError):
            return None, 'File not Found'
        

# Read and clean up the PDF data

def read_pdf_data(pdf_path):
    reader, error = open_pdf(pdf_path)
    if reader is None:
        return None, error
    transit_data = [page.extract_text() for page in reader.pages]
    t1_data = "\n".join(transit_data)
    return t1_data, None


def data_filter(pdf_path):
    t1_data, error = read_pdf_data(pdf_path)
    if error:
        return None, error
    mrn_match = re.search(r'\d{2}CH[A-Z0-9]+', t1_data)
    shipment_match = re.search(r'\d{11}', t1_data)
    transit_document = {
        'MRN-Nummer': mrn_match.group() if mrn_match else None,
        'Sendungsnummer': shipment_match.group() if shipment_match else None,
        'Anzahl Packstücke': '',
        'Gewicht': '',
        'Zollstelle': '',
    }
    return transit_document, None


def main(pdf_path):
    result, error = data_filter(pdf_path)
    if error:
        print(f'Fehler: {error}')
    else:
        print(f'Transit Daten: {result}')


if __name__ == "__main__":
    main('/Users/Jonas_1/Documents/Jonas/Informatik/Projekt_WA/project_wa/Python_Back_End/t1_reader/MRN_25CH02GBIXU8MM7NJ0.pdf')