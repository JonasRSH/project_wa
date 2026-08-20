"""Hilfsskript: Gibt den Rohtext eines T1-PDFs aus und zeigt was jedes Muster findet."""
import sys
import re
from pypdf import PdfReader


def main(pdf_path):
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    print("=" * 70)
    print("ROHTEXT (erste 3000 Zeichen):")
    print("=" * 70)
    print(text[:3000])
    print()

    patterns = {
        "MRN":              r'\d{2}CH[A-Z0-9]+',
        "Sendungsnummer":   r'Sendungsnummer[^\d]*(\d{11})',
        "Sendungsnr.-FB":   r'\d{11}',
        "Packst.insgesamt": r'Packst\. insgesamt[\s\S]{0,200}',
        "Gesamte Rohmasse": r'Gesamte Rohmasse[\s\S]{0,200}',
        "Warenbez.-Kontext":r'(?:Warenbezeichnung|BEZEICHNUNG DER WAREN)[\s\S]{0,300}',
        "Semikolon-Zeilen": r'.{0,5};\s*[A-Z]{2,4}\s*;.{0,60}',
        "BESTIMMUNGSSTELLE":r'BESTIMMUNGSSTELLE[\s\S]{0,200}',
    }

    print("=" * 70)
    print("MUSTER-TREFFER:")
    print("=" * 70)
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text)
        print(f"\n[{name}]  ({len(matches)} Treffer)")
        for m in matches[:3]:
            print("  >>", repr(m[:120]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python3 debug_t1.py <pfad/zu/t1.pdf>")
    else:
        main(sys.argv[1])
