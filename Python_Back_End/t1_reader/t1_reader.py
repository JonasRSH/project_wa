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
    colli_no_match = re.search(r'Packst\. insgesamt[\s\S]*?\d+\s+(\d+)\s+[^\s]+\.\d{3}', t1_data)
    gewicht_match = re.search(r'Gesamte Rohmasse[\s\S]*?\d+\s+\d+\s+([^\s]+\.\d{3})', t1_data)
    zollstelle_match = re.search(r'BESTIMMUNGSSTELLE[\s\S]*?CH\d+\s+([^,\n]+)', t1_data)
    transit_document = {
        'MRN-Nummer': mrn_match.group() if mrn_match else None,
        'Sendungsnummer': shipment_match.group() if shipment_match else None,
        'Anzahl Packstücke': colli_no_match.group(1) if colli_no_match else None,
        'Gewicht': gewicht_match.group(1) if gewicht_match else None,
        'Zollstelle': zollstelle_match.group(1) if zollstelle_match else None,
    }
    return transit_document, None


def main(pdf_path):
    result, error = data_filter(pdf_path)
    if error:
        print(f'Fehler: {error}')
    else:
        print(f'Transit Daten: {result}')


if __name__ == "__main__":
    main('/Users/Jonas_1/Documents/Jonas/Informatik/Projekt_WA/project_wa/Python_Back_End/t1_reader/MRN_26CH05WTL3TJWMS5J1.pdf')