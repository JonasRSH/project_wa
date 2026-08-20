from pypdf import PdfReader
import re


def _compact(text):
    return re.sub(r'\s+', ' ', text or '').strip()


# Seite 2 Packstücke-Format: Menge;TYP;Nummerncode (mind. 5 Stellen)
_COLLI_RE = r'\b(\d+)\s*;\s*([A-Z]{2,4})\s*;\s*(\d{5,})'


def _extract_goods_description(t1_data):
    # Schweizer T1-Formularcodes wie [13 02] markieren Kopfzeilen – diese ausschließen
    def _is_form_header(text):
        return bool(re.search(r'\[\d{2}[\s_]\d{2}\]', text))

    # 1. Text direkt nach Packstücke-Eintrag (N;TYP;CODE Text) auf derselben Zeile
    m = re.search(_COLLI_RE + r'\s+([A-Za-z\u00c0-\u024f][^\n]{2,})', t1_data)
    if m and not _is_form_header(m.group(4)):
        return _compact(m.group(4))
    # 2. Label "Beschreibung der Waren" (Seite 2, Pos. 1)
    m = re.search(r'Beschreibung der Waren[^\n:]*:?\s*([^\n]{3,})', t1_data, re.IGNORECASE)
    if m and not _is_form_header(m.group(1)):
        return _compact(m.group(1))
    return None


def _extract_colli_type(t1_data):
    m = re.search(_COLLI_RE, t1_data)
    return m.group(2) if m else None


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
    # Schweizer Tausender-Apostroph (U+2019) → normaler Apostroph
    t1_data = t1_data.replace('\u2019', "'")
    return t1_data, None


def data_filter(pdf_path):
    t1_data, error = read_pdf_data(pdf_path)
    if error:
        return None, error
    mrn_match = re.search(r'\d{2}CH[A-Z0-9]+', t1_data)
    shipment_match = re.search(r'Sendungsnummer[^\d]*(\d{11})', t1_data, re.IGNORECASE)
    if not shipment_match:
        shipment_match = re.search(r'\d{11}', t1_data)
    expo_shipment_nos = re.findall(r'EXPO;[^;\n]+;(\d{11})', t1_data)
    # Seite 1: "Packst. insgesamt" und "Gesamte Rohmasse" aus der Header-Folgezeile
    # Format: Header-Zeile "...Packst. insgesamt Gesamte Rohmasse..."
    #          Nächste Zeile: Empfängername {Positionen} {Packst.ges.} {Rohmasse} {Sicherheit}
    summary_match = re.search(
        r'Packst\.\s*insgesamt[^\n]*\n[^\n]*?(\d+)\s+(\d+)\s+([\d\']+\.\d+|[\d\']{2,})',
        t1_data
    )
    colli_qty = int(summary_match.group(2)) if summary_match else None
    zollstelle_match = re.search(r'BESTIMMUNGSSTELLE[\s\S]*?CH\d+\s+([^,\n]+)', t1_data)
    goods_description = _extract_goods_description(t1_data)
    colli_type = _extract_colli_type(t1_data)
    transit_document = {
        'MRN-Nummer': mrn_match.group() if mrn_match else None,
        'Sendungsnummer': shipment_match.group(1) if shipment_match and shipment_match.lastindex else (shipment_match.group() if shipment_match else None),
        'Sendungsnummern': expo_shipment_nos,
        'Anzahl Packstücke': str(colli_qty) if colli_qty is not None else None,
        'Colli-Typ': colli_type,
        'Warenbeschreibung': goods_description,
        'Gewicht': summary_match.group(3) if summary_match else None,
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