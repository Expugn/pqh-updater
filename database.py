import os
import wget
import brotli
import sqlite3


class Database:
    def __init__(self):
        self.data_directory = 'data'
        self.redive_db_path = self.data_directory + '/redive_jp.db.br'
        self.output_db_path = self.data_directory + '/redive_jp.db'
        self.redive_db_url = 'https://redive.estertion.win/db/redive_jp.db.br'
        self.connection = None
        self.init_database()

    def __del__(self):
        if self.connection is not None:
            self.close_connection()
        if os.path.exists('data/redive_jp.db.br'):
            os.remove('data/redive_jp.db.br')
        if os.path.exists('data/redive_jp.db'):
            os.remove('data/redive_jp.db')

    # DECOMPRESS BROTLI COMPRESSED FILES
    @staticmethod
    def brotli_decompress(input_file_path, output_file_path):
        open(output_file_path, 'wb').write(brotli.decompress(open(input_file_path, 'rb').read()))
        print('Decompressed ' + input_file_path + ' and output file to ' + output_file_path)

    # IF DATABASE FILES DO NOT EXIST, DOWNLOAD LATEST
    def init_database(self):
        # CHECK IF REDIVE_DB EXISTS
        if not os.path.exists(self.redive_db_path):
            print(self.redive_db_path + " not found! Grabbing latest version...")
            self.get_database()

        # CHECK IF DECOMPRESSED REDIVE_DB EXISTS
        if not os.path.exists(self.output_db_path):
            print(self.output_db_path + " not found! Decompressing " + self.redive_db_path + "...")
            self.brotli_decompress(self.redive_db_path, self.output_db_path)

    # DOWNLOADS LATEST DATABASE
    def get_database(self):
        # CHECK IF REDIVE_DB EXISTS ; DELETE IF SO
        if os.path.exists(self.redive_db_path):
            os.remove(self.redive_db_path)

        # CHECK IF OUTPUT_DB EXISTS ; DELETE IF SO
        if os.path.exists(self.output_db_path):
            os.remove(self.output_db_path)

        # DOWNLOAD REDIVE_JP.DB.BR
        print('Downloading ' + self.redive_db_path + ' from ' + self.redive_db_url)
        wget.download(self.redive_db_url, self.redive_db_path)

        # DECOMPRESS REDIVE_JP.DB.BR VIA BROTLI DECOMPRESSION
        self.brotli_decompress(self.redive_db_path, self.output_db_path)

    def get_cursor(self):
        # CHECK IF CONNECTION IS ALREADY ESTABLISHED
        if self.connection is None:
            self.connection = sqlite3.connect(self.output_db_path)

        return self.connection.cursor()

    def close_connection(self):
        # CHECK IF CONNECTION IS ESTABLISHED
        if self.connection is not None:
            self.connection.close()
            self.connection = None
