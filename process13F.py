#!/usr/bin/env python

"""Process parsed 13F to csv**for educational purposes only. MIT License"""

__author__      = "Aneesh Panoli"
__copyright__   = "MIT License"


import pandas as pd
import os
from institutionList import institutions
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class process13FHR:
    def __init__(self):
        self.df13FdataFname = "csv/StockOwnership/13Fdata.csv"
        self.df13FdataFnamePath = os.path.join(BASE_DIR, self.df13FdataFname)
        self.df13Fdata = pd.read_csv(self.df13FdataFnamePath, encoding = "ISO-8859-1")
        self.columns = self.df13Fdata.columns
        self.dataList = self.df13Fdata.values.tolist()
    def institution_of_interest(self):
        insti = str(input("Please enter the Institution name: ")).lower()
        return self.df13Fdata.head()
    def com_of_interest(self):
        com = str(input("Please enter the company name: ")).lower()
        comCsv = "csv/StockOwnership/13Fdata_"+com+".csv"
        comCsvPath = os.path.join(BASE_DIR, comCsv)
        coms = [row for row in self.dataList for s in row if com in str(s).lower()]
        if coms != []:
            comDf = pd.DataFrame(coms, columns=self.columns)
            comDf.to_csv(comCsvPath, sep=',', index=False, encoding = "utf-8")
            return com+" has been saved!"
        else:
            return com+" doesn't exist in the database"
if __name__ == '__main__':
    start13Fprocess = process13FHR()
    print(start13Fprocess.com_of_interest())
