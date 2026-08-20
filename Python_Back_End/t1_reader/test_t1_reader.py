import os
import pytest
from unittest.mock import MagicMock, patch
from t1_reader import open_pdf, read_pdf_data, data_filter

PDF_PATH = os.path.join(os.path.dirname(__file__), 'MRN_26CH05WTL3TJWMS5J1.pdf')
PDF_AVAILABLE = os.path.exists(PDF_PATH)


# ---------------------------------------------------------------------------
# open_pdf
# ---------------------------------------------------------------------------

def test_open_pdf_file_not_found():
    reader, error = open_pdf('nicht_vorhanden.pdf')
    assert reader is None
    assert error == 'File not Found'


@pytest.mark.skipif(not PDF_AVAILABLE, reason='Test-PDF nicht vorhanden')
def test_open_pdf_success():
    reader, error = open_pdf(PDF_PATH)
    assert error is None
    assert reader is not None


# ---------------------------------------------------------------------------
# read_pdf_data  (mit Mock)
# ---------------------------------------------------------------------------

def test_read_pdf_data_propagates_error():
    with patch('t1_reader.open_pdf', return_value=(None, 'File not Found')):
        data, error = read_pdf_data('dummy.pdf')
    assert data is None
    assert error == 'File not Found'


def test_read_pdf_data_joins_pages():
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = 'Seite 1'
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = 'Seite 2'
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page1, mock_page2]

    with patch('t1_reader.open_pdf', return_value=(mock_reader, None)):
        data, error = read_pdf_data('dummy.pdf')

    assert error is None
    assert data == 'Seite 1\nSeite 2'


# ---------------------------------------------------------------------------
# data_filter  (mit Mock-Text)
# ---------------------------------------------------------------------------

SAMPLE_T1_TEXT = (
    'Packst. insgesamt Gesamte Rohmasse Sicherheit [11 07]\n'
    'IDC Worms 61 32 10\u2019121.996 0\n'
    'MRN 26CH05WTL3TJWMS5J1\n'
    '04964788310 Scintilla\n'
    'ABGANGSSTELLE [17 03] BESTIMMUNGSSTELLE (UND LAND) [17 05]\n'
    'Zoll Mitte - Bern;CH001661 Rheinfelden-Autobahn,DE\n'
)


def test_data_filter_returns_error_on_missing_file():
    result, error = data_filter('nicht_vorhanden.pdf')
    assert result is None
    assert error is not None


def test_data_filter_extracts_all_fields():
    with patch('t1_reader.read_pdf_data', return_value=(SAMPLE_T1_TEXT, None)):
        result, error = data_filter('dummy.pdf')

    assert error is None
    assert result['MRN-Nummer'] == '26CH05WTL3TJWMS5J1'
    assert result['Sendungsnummer'] == '04964788310'
    assert result['Anzahl Packstücke'] == '32'
    assert result['Zollstelle'] == 'Rheinfelden-Autobahn'


def test_data_filter_none_on_missing_mrn():
    text = 'kein MRN hier, keine Sendungsnummer, kein T1'
    with patch('t1_reader.read_pdf_data', return_value=(text, None)):
        result, error = data_filter('dummy.pdf')
    assert error is None
    assert result['MRN-Nummer'] is None
    assert result['Anzahl Packstücke'] is None


# ---------------------------------------------------------------------------
# Integration – echter PDF-File
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not PDF_AVAILABLE, reason='Test-PDF nicht vorhanden')
def test_integration_real_pdf():
    result, error = data_filter(PDF_PATH)
    assert error is None
    assert result['MRN-Nummer'] == '26CH05WTL3TJWMS5J1'
    assert result['Sendungsnummer'] == '04964788310'
    assert result['Anzahl Packstücke'] == '32'
    assert result['Zollstelle'] == 'Rheinfelden-Autobahn'
