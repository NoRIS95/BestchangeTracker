import os
from dotenv import load_dotenv

load_dotenv()


class Table:
    def __init__(self):
        self.__spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.__sheet_name = os.getenv('SHEET_NAME')
        self.__credentials_file = os.getenv('CREDENTIALS_FILE', 'secret.json')
    
    def get_spreadsheet_id(self):
        return self.__spreadsheet_id
    
    def get_sheet_name(self):
        return self.__sheet_name
    
    def get_credentials_file(self):
        return self.__credentials_file
