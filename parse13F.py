#!/usr/bin/env python

"""Process SEC-EDGAR 13F **for educational purposes only. MIT License"""

__author__      = "Aneesh Panoli"
__copyright__   = "MIT License"

from bs4 import BeautifulSoup as bs
import os
import re
import urllib
import pandas as pd
from institutionList import institutions
import time, datetime
from dateutil.relativedelta import relativedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_form_13F():

    #-----------re compilers-------------------------------------------
    # t1 = time.time()
    rawstring = re.compile(r'<[\s\S]*?>') # general tag remover
    rawstringfilingref = re.compile(r'<[\s\S]*?>|\s') # general tag remover
    rawstringsecName = re.compile(r'<[\s\S]*?>|\*|/|\\|\'|"|\?|!') # format securties name from  13F-HR
    rawFindtAhref = re.compile(r'href="[\s\S]*?>') # find href links
    rawSubAhref = re.compile(r'href="|">|\s') # remove a href tags
    rawFindFilingDate = re.compile(r'Filing Date</div>\n<div class="info">[\s\S]*?</div>')
    rawSubFilingDate = re.compile(r'Filing Date</div>\n<div class="info">|</div>')

    #get list of ciks/institution names from the master institutions.csv--------------------------------------
    instituionsFname = "csv/StockOwnership/institutions.csv"
    instituionsPath = os.path.join(BASE_DIR, instituionsFname)
    institutionsDf = pd.read_csv(instituionsPath)#, skiprows=range(1,14))
    cikList = institutionsDf['cik'].tolist()
    instNameList = institutionsDf['name'].tolist()
    # look for filing information
    # iterate through the CIK number and look for 13F-HR filing info from SEC max 10 filings
    # parse the resulting page and  extract links to individual filing page. This is not-
    # the link to `3F form ` itself. Just a pointer to the filing page
    # make the list
    for ind, cik in enumerate(cikList):
        linkList = []
        urlCheckIf13F = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)\
                        +"&type=13F-HR&output=xml&dateb=20180101&owner=exclude&count=10"
        with urllib.request.urlopen(urlCheckIf13F) as f:
            soup = bs(f, 'lxml')
            if "filinghref" in str(soup):
                for i in soup.findAll('filinghref'):
                    linkList.append(re.sub(rawstringfilingref, '', str(i)+"l"))
            else:
                name = "No filings exist"
        # iterate through each link in the link list
        # parse the page to extract links to actual form 13F-HR
        # also extract the filing dates to use as the column names
        for link in linkList:
            xmlLinkList = []
            try:
                with urllib.request.urlopen(link) as xmlf:
                    soup1 = bs(xmlf, 'lxml')
            except:
                print("HTTP 404 error, moving on to next intitution...")
                time.sleep(1)
                break
            for i in soup1.findAll("tr", { "class" : "blueRow" }):
                if "INFORMATION TABLE" in str(i):
                    xmlLinkList.append("https://www.sec.gov"+re.sub(rawSubAhref, '', re.findall(rawFindtAhref, str(i))[0]))

            filingDate = re.sub(rawSubFilingDate, '', re.findall(rawFindFilingDate, str(soup1))[0]).strip()[:8]
            # filingDate = re.findall(rawFindFilingDate, str(soup1))
            print("Institution:", instNameList[ind], cik,". (", ind+1, "of", len(cikList), ")")
            print(xmlLinkList)
            print (filingDate)
            time.sleep(1)
            if xmlLinkList == []:
                break
            columns = ['cik', 'institution']
            columns.extend(monthList())
            filingDateMax = "2015-01"
            #iterate through xmllink list
            # parse each page and extract security name and no of shares held
            if time.mktime(datetime.datetime.strptime(filingDate,"%Y-%m").timetuple())\
                >time.mktime(datetime.datetime.strptime(filingDateMax,"%Y-%m").timetuple()):
                for k in xmlLinkList:
                    print("filing date is after", filingDateMax)
                    securitesNames = []
                    noOfShareList = []
                    cusips = []
                    with urllib.request.urlopen(k) as xmls:
                        soup2 = bs(xmls, 'lxml')
                    for l in soup2.findAll('nameofissuer'):
                        l = str(l).replace("&amp;", "and")
                        securitesNames.append(re.sub(rawstringsecName, ' ', l).strip())
                    for m in soup2.findAll('sshprnamt'):
                        noOfShareList.append(re.sub(rawstring, '', str(m)))
                    for c in soup2.findAll('cusip'):
                        cusips.append(re.sub(rawstring, ' ', str(c)).strip())

                    # iterate through the extracted securities name list
                    # create csv for each security
                    # insert the institution name , CIK, filing date as coulmn and shares held
                    # make pandas DataFrame
                    for indx, secName in enumerate(securitesNames):
                        # create a list of insitution owned securities while parsing 13F-HR form
                        print(secName, end='\r')
                        listOfInstOwnedSecs = "csv/StockOwnership/securitieslist.csv"
                        listOfInstOwnedSecsPath = os.path.join(BASE_DIR, listOfInstOwnedSecs)
                        try:
                            securityListDf = pd.read_csv(listOfInstOwnedSecsPath, converters={'cusip': lambda x: str(x)})
                            securityNameList = securityListDf['name'].tolist()
                            cusipList = securityListDf['cusip'].tolist()
                        except:
                            securityListDf = pd.DataFrame(columns=['name', 'cusip'])
                            securityNameList = securityListDf['name'].tolist()
                            cusipList = securityListDf['cusip'].tolist()
                        #_-----------------------------------
                        if cusips[indx] not in cusipList:
                            securityListDf.loc[len(securityListDf.index)] = [secName, cusips[indx]]
                        else:
                            secName = securityNameList[cusipList.index(cusips[indx])]
                        securityFname = "csv/StockOwnership/13F/"+secName+".csv"
                        securityFnamePath = os.path.join(BASE_DIR, securityFname)
                        try:
                            securitydf = pd.read_csv(securityFnamePath)
                            columnHeader = list(securitydf)
                            institutionList = securitydf['institution'].tolist()
                            if filingDate not in columnHeader:
                                securitydf[filingDate] = 0
                        except:
                            securitydf = pd.DataFrame(columns=columns)
                            institutionList = securitydf['institution'].tolist()
                        indexToInsert = len(securitydf.index)
                        #print(indexToInsert)
                        # if an institution name doesnt exisit in a security spreadsheet add it to it
                        if instNameList[ind] not in institutionList:
                            #print("Adding",instNameList[ind], "to", secName )
                            securitydf.loc[indexToInsert] = 0
                            securitydf.loc[indexToInsert, 'cik'] = cik
                            securitydf.loc[indexToInsert, 'institution'] = instNameList[ind]
                            securitydf.loc[indexToInsert, filingDate] = noOfShareList[indx]
                            securitydf.to_csv(securityFnamePath, sep=',', index=False)
                        elif instNameList[ind] in institutionList:
                            #print("Exists",instNameList[ind], "adding shares to", secName )
                            sharesAlreadyOwn = securitydf[filingDate].iloc[institutionList.index(instNameList[ind])]
                            securitydf[filingDate].iloc[institutionList.index(instNameList[ind])] = sharesAlreadyOwn + int(noOfShareList[indx])
                            securitydf.to_csv(securityFnamePath, sep=',', index=False)

        #save intitution owned securoties name list
                        securityListDf.to_csv(listOfInstOwnedSecsPath, sep=',', index=False)
                    # t2 = time.time()
                    print("Time elapsed:", t2-t1)
def monthList():
    result = []
    today = datetime.date.today()
    current = datetime.date(2015, 1, 1)
    while current <= today:
        result.append(current.strftime("%Y-%m"))
        current += relativedelta(months=1)
    return result[::-1]

if __name__ == '__main__':
    parse_form_13F()
# run with 'nohup python -u ./cmd.py > cmd.log &'
#use 'ps -ef' to get pID
# then 'kill pid' to terminate nohup
# tail folder 'watch "ls -lrt | tail -10"'
#empty dir 'rm -r folder/*''
