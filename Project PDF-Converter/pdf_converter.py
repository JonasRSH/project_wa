from PyPDF2 import PdfReader
import re
import pandas as pd
from openpyxl import load_workbook


def open_pdf(pdf_path):
    try:
        pdf_file = PdfReader(pdf_path, 'r')
        return pdf_file, None
    except(FileNotFoundError):
        return None, 'File not Found'


def read_pdf(pdf_path):
    pdf_file, error_message = open_pdf(pdf_path)
    if pdf_file is None:
        return []
    for page in pdf_file.pages:
        data_from_pdf = page.extract_text()
        if not data_from_pdf:
            continue
        return data_from_pdf


def main():
    pdf_path = input('PDF Filename: ')
    pdf_file = open_pdf()
    pdf_data = read_pdf()
    print(pdf_data)


if __name__ == "__main__":
    main()
