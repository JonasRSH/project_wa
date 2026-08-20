from pypdf import PdfReader
import re


def _compact(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def _extract_goods_description(t1_data):
    patterns = [
        r'Warenbezeichnung(?: der Waren)?\s*[:\-]?\s*([^\n]+)',
        r'BEZEICHNUNG DER WAREN\s*[:\-]?\s*([^\n]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, t1_data, re.IGNORECASE)
        if match:
            value = _compact(match.group(1))
            if value:
                return value
    return None


def _extract_colli_type(t1_data):
    patterns = [
        r'Packst\. insgesamt[\s\S]*?\b\d+\s+([A-Z]{2,4})\s+\d+[\d\'’\.]*',
        r'Packst\. insgesamt[\s\S]*?\b([A-Z]{2,4})\s+\d+\s+\d+[\d\'’\.]*',
    ]
    for pattern in patterns:
        match = re.search(pattern, t1_data)
        if match:
            return match.group(1)
    return None


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
    shipment_match = re.search(r'Sendungsnummer[^\d]*(\d{11})', t1_data, re.IGNORECASE)
    if not shipment_match:
        shipment_match = re.search(r'\d{11}', t1_data)
    colli_no_match = re.search(r'Packst\. insgesamt[\s\S]*?\d+\s+(\d+)\s+[^\s]+\.\d{3}', t1_data)
    gewicht_match = re.search(r'Gesamte Rohmasse[\s\S]*?\d+\s+\d+\s+([^\s]+\.\d{3})', t1_data)
    zollstelle_match = re.search(r'BESTIMMUNGSSTELLE[\s\S]*?CH\d+\s+([^,\n]+)', t1_data)
    goods_description = _extract_goods_description(t1_data)
    colli_type = _extract_colli_type(t1_data)
    transit_document = {
        'MRN-Nummer': mrn_match.group() if mrn_match else None,
        'Sendungsnummer': shipment_match.group(1) if shipment_match and shipment_match.lastindex else (shipment_match.group() if shipment_match else None),
        'Anzahl Packstücke': colli_no_match.group(1) if colli_no_match else None,
        'Colli-Typ': colli_type,
        'Warenbeschreibung': goods_description,
        'Gewicht': gewicht_match.group(1) if gewicht_match else None,
        'Zollstelle': _compact(zollstelle_match.group(1)) if zollstelle_match else None,
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