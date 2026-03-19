from PyPDF2 import PdfReader
import re
import pandas as pd
from openpyxl import load_workbook


# Class which represents a shipment and handles the containing data
class Shipment():
    def __init__(self, position, shipment_no, exporter, colli_no, colli_type, content, weight, customs_handling):
        self.position = position
        self.shipment_no = shipment_no
        self.exporter = exporter
        self.colli_no = colli_no
        self.colli_type = colli_type
        self.content = content
        self.weight = weight
        self.customs_handling = customs_handling
            
    # Opens the PDF Shipment-List (Abmeldeliste) with the PyPDF2 Library
    @staticmethod
    def open_checklist(pdf_path):
        try:
            reader = PdfReader(pdf_path, 'r')
            return reader, None
        except(FileNotFoundError):
            return None, 'File not Found'
        

    # Read and clean up the PDF data, which is a List of shipments with several pages and shipment informations
    @staticmethod
    def read_pdf_data(pdf_path):
        shipment_data_list = []
        reader, error_message = Shipment.open_checklist(pdf_path)
        if reader is None:
            return []
        for page in reader.pages:
            checklist_data = []
            data_from_pdf = page.extract_text()
            if not data_from_pdf:
                continue  # Leere Seite überspringen
            pdf_data = data_from_pdf.replace('-', '') 
            data_list = pdf_data.split('\n\n')

            for i in data_list:
                if i.startswith('0'):
                    checklist_data.append(i)
            for data in checklist_data:
                shipment_data = data.replace('     ',',').replace('\n', ',').replace('Bf','kg,').split('\n')
                for pdf_data in shipment_data:
                    shipment_data_list.append(pdf_data)
        return shipment_data_list

#Extract list position from data
    @staticmethod
    def get_position(d):
        position = (d[0:3])
        return position

    #Extract shipment number from data
    @staticmethod
    def get_shipment_no(d):
        shipment_no = d[3:14]
        return shipment_no

    #Exctract exporter from data
    @staticmethod
    def get_exporter(d):
        exporter_data = d[14:44].split(',')
        exporter = exporter_data[0].split()[0]
        return exporter

    #Exctract colli number from data
    @staticmethod
    def get_colli_no(d):
        colli = 'KT|EW|EU|KI|ZK|GB|PA|BX|DR|PH|HE'
        pattern = rf'(0[0-9]{{2}})(.*,)([0-9]{{1,3}}) ({colli})'
        matches = re.finditer(pattern, d)
        colli_no = 0
        for match in matches:
            collies = int(match.group(3))
            colli_no += collies
            return colli_no

    #Exctract colli type from data
    @staticmethod
    def get_colli_type(d):
        colli = 'KT|EW|EU|KI|ZK|GB|PA|BX|DR|PH|HE'
        pattern = rf'(0[0-9]{{2}})(.*,)([0-9]{{1,3}}) ({colli})'
        match = re.search(pattern, d)
        if match:
            colli_type = match.group(4)
            return colli_type


    #Extract conent from data
    @staticmethod
    def get_content(d):
        content_list = []
        content_data = d[45:100].split(' ')
        for content in content_data:
            if content.isalpha():
                if len(content) > 2:
                    content_list.append(content)
                    return content


    #Extract weight from data
    @staticmethod
    def get_weight(d):
        weight_pattern = rf'([0-9]{{1,5}}) (kg)'
        weight_match = re.finditer(weight_pattern, d)
        weight = 0
        for match in weight_match:
            weights = int(match.group(1))
            weight += weights
            return weight


    #Extracts customs handling from data
    @staticmethod
    def get_customs_handling(d):
        handling_list_pattern = r'kg, (EDEC|M90)/(EUR1.*?)?/?(EUVZ|GVZ|ATA|ET1|ST1)?/?((ST1|ET1))?'
        handling_matches = re.search(handling_list_pattern, d)
        if handling_matches:
            customs_handling = []
            customs_handling.append(handling_matches.group(1,2,3,4))
        else:
            customs_handling = ['! No customs handling ! Please verify...']
        return customs_handling
    
    # Return True if the shipment is valid (not 'ZK'), False otherwise
    @staticmethod
    def is_valid_shipment(colli_type):
        return colli_type != 'ZK'
    
    # Calculates them sum of all Collies
    @staticmethod
    def calculate_total_collies(shipment_list):
        total_collies = sum(shipment.colli_no for shipment in shipment_list)
        return total_collies
    
    @staticmethod
    def calculate_total_weight(shipment_list):
        total_weight = sum(shipment.weight for shipment in shipment_list)
        return total_weight

    # Creates a shipment with the from the PDF extracted data
    @classmethod
    def create_shipment(cls, pdf_path):
        shipment_data = cls.read_pdf_data(pdf_path)
        shipment_list = []
        for d in shipment_data:
            shipment = cls(
                position=cls.get_position(d),
                shipment_no=cls.get_shipment_no(d),
                exporter=cls.get_exporter(d),
                colli_no=cls.get_colli_no(d),
                colli_type=cls.get_colli_type(d),
                content=cls.get_content(d),
                weight=cls.get_weight(d),
                customs_handling=cls.get_customs_handling(d)
            )
            if cls.is_valid_shipment(shipment.colli_type):
                shipment_list.append(shipment)
        return shipment_list
    
    def __str__(self):
        return (
            f'Shipment No: {self.shipment_no} | '
            f'Colli No: {self.colli_no} | '
            f'Colli Type: {self.colli_type} | '
            f'Content: {self.content} | '
            f'Weight: {self.weight} | '
            f'Customs Handling: {self.customs_handling}'
        )


    # Öffnet die Excel-Datei 'warenausweis.xlsx', trägt die Daten ein und speichert sie wieder ab
    def create_excel(self, filename=None, abfahrt_name=None, datum=None, kennzeichen=None, anhaenger=None, zollamt_abgang=None, zollamt_grenz=None):
        import os
        import re
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # Vorlage immer gleich, nie überschreiben
        vorlage = os.path.join(base_dir, 'Python_Back_End', 'loading_list_check', 'warenausweis.xlsx')
        if abfahrt_name is None:
            abfahrt_name = ''
        if datum is None:
            from datetime import datetime
            datum = datetime.now().strftime('%Y-%m-%d')
        if kennzeichen is None:
            kennzeichen = ''
        if anhaenger is None:
            anhaenger = ''
        if zollamt_abgang is None:
            zollamt_abgang = ''
        if zollamt_grenz is None:
            zollamt_grenz = ''
        neuer_name = f"WA {abfahrt_name} {datum}.xlsx"
        # Entferne problematische Zeichen aus dem Dateinamen
        neuer_name = re.sub(r'[\\/:"*?<>|()]+', '', neuer_name)
        neuer_pfad = os.path.join(base_dir, 'Python_Back_End', 'loading_list_check', neuer_name)
        # Vorlage kopieren
        import shutil
        shutil.copy(vorlage, neuer_pfad)
        wb = load_workbook(neuer_pfad)
        sheetnames = ['Tabelle 1', 'Tabelle1', 'Tabelle 2', 'Tabelle2', 'Tabelle 3', 'Tabelle3']
        print('DEBUG: Vorhandene Sheets:', wb.sheetnames)
        for sheetname in sheetnames:
            if sheetname in wb.sheetnames:
                print(f'DEBUG: Schreibe Daten in {sheetname}')
                ws = wb[sheetname]
                # Abfahrt in E1
                if abfahrt_name:
                    ws['E1'] = abfahrt_name
                # Motorwagen-Kennzeichen in H3
                if kennzeichen:
                    ws['H3'] = kennzeichen
                # Anhänger-Kennzeichen in H4
                if anhaenger:
                    ws['H4'] = anhaenger
                # Grenzzollamt in B1
                if zollamt_grenz:
                    ws['B1'] = zollamt_grenz
                # Datum in B4
                if datum:
                    ws['B4'] = datum
                # Abgangszollamt (B2) wird erst später eingetragen, daher hier nicht automatisch setzen
                start_row = 6
                start_col = 2
                merges_to_remove = []
                for merged_range in ws.merged_cells.ranges:
                    min_col, min_row, max_col, max_row = merged_range.bounds
                    if min_row >= start_row and min_col >= start_col:
                        merges_to_remove.append(merged_range)
                for merged_range in merges_to_remove:
                    ws.unmerge_cells(str(merged_range))
                for index, shipment in enumerate(self.shipment_list):
                    row = start_row + index
                    ws.cell(row=row, column=start_col, value=shipment.shipment_no)
                    ws.cell(row=row, column=start_col + 1, value=shipment.colli_no)
                    ws.cell(row=row, column=start_col + 2, value=shipment.colli_type)
                    ws.cell(row=row, column=start_col + 3, value=shipment.content)
                    ws.cell(row=row, column=start_col + 4, value=shipment.weight)
        wb.save(neuer_pfad)

def main():
    pdf_path = "/Users/Jonas_1/Documents/Jonas/Informatik/Projekt_WA/Python_Back_End/loading_list_check/abmeldeliste.pdf" 
    shipment_list = Shipment.create_shipment(pdf_path)
    for shipment in shipment_list:
        if shipment_list:
            shipment_list[0].shipment_list = shipment_list
            shipment_list[0].create_excel()
    print(f'Total Collies: {Shipment.calculate_total_collies(shipment_list)} Total Weight: {Shipment.calculate_total_weight(shipment_list)}')
    

if __name__ == "__main__":
    main()