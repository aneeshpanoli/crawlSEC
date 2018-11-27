from bs4 import BeautifulSoup as bs
import os
import re
import urllib
import pandas as pd
from institutionList import institutions
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SecEdgarCrawler():
    def __init__(self):
        pass
    def get_valid_13F_HR_ciks(self): # Only those CIKs of 13F filers
        '''This script can get the CIKs and names of anyone who file 13F_HR connected to given keyword'''

        filename = "csv/StockOwnership/institutions.csv"
        csvPath = os.path.join(BASE_DIR,  filename)
        columns = ['cik', 'name', 'sic', 'sicdiscription', 'siclink']
        # choose = input("Please Enter 1 to add a single institution to the institutions list or 2 add a  list: ")
        # if choose == "1":
        #     comNames = [input("Please enter the company name/Keyword: ")]
        # else:
        comNames = institutions()
        for kw in comNames:
            print(kw)
            comName = kw.strip().lower()
            comName = comName.replace(' ', "+")
            url = "https://www.sec.gov/cgi-bin/browse-edgar?company="+comName+"&owner=exclude&output=xml&action=getcompany"
            with urllib.request.urlopen(url) as f:
                soup =bs(f, 'lxml')
            ciks = re.findall(r'CIK=[\s\S]*?&amp', str(soup))
            rawstring = re.compile(r'<[\s\S]*?>')
            rawstrinNameSub = re.compile(r'<[\s\S]*?>|/|"')
            for i in ciks:
                time.sleep(1)
                cik = re.sub(r'CIK=|&amp', '', i)
                try:
                    df = pd.read_csv(csvPath, converters={'cik': lambda x: str(x)}) # converter was added retain left side zeros
                except:
                    df = pd.DataFrame(columns=columns)
                cikList = df['cik'].tolist()
                if cik not in cikList:
                    for j in ["13F-HR"]:#, "13G", "13D"]:
                        urlCheckIf13F = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+cik+"&type="+j+"&output=xml&dateb=20180101&owner=exclude&count=10"#"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+i+"&type=13F&dateb=20180101&owner=exclude&output=xml&count=10"
                        with urllib.request.urlopen(urlCheckIf13F) as v:
                            soup1 = bs(v, 'xml')
                            if "filingHREF" in str(soup1):
                                name = re.sub(rawstrinNameSub, ' ', str(soup1.find('name'))).strip()
                                name = name.replace("&amp;amp;amp;","and")
                                name = name.replace("&amp;","and")
                                sic = re.sub(rawstring, '', str(soup1.find('SIC'))).strip()
                                sic_disc = re.sub(rawstring, '', str(soup1.find('SICDescription')))
                                sic_link = re.sub(rawstring, '', str(soup1.find('SICHREF')))
                                df.loc[len(df.index)] = [cik, name, sic, sic_disc, sic_link]
                                df.to_csv(csvPath, sep=',', index=False)
                            else:
                                name = "No filings exist"
                    # try:

                    # except:
                        # print(name)
                else:
                    print("Already in the database! ")
job = SecEdgarCrawler()
job.get_valid_13F_HR_ciks()
