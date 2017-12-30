#!/usr/local/bin/python3.6

import os, sys, glob
from zipfile import ZipFile
from math import ceil
from bs4 import BeautifulSoup
if sys.version_info > (3, 0):
    from urllib import request
    from urllib.request import urlopen
else:
    from urllib3 import request
    from urllib3.request import *

def clearScreen ():
    os.system ('cls' if os.name == 'nt' else 'clear')
    return

def getFileRating (ratingStr):
    if ratingStr.find ('neutral-icon') >= 0:
        rating = 'UR'
    elif ratingStr.find ('positive-icon') >= 0:
        rating = 'OK'
    elif ratingStr.find ('bad-icon') >= 0:
        rating = 'X'
    return rating

def getSubtitleList (titleDict):
    global url, header
    subtitleDict = dict ()
    targetUrl = url + titleDict['titleLink']
    urlReq  = request.Request (targetUrl, headers=header)
    dataDiv = BeautifulSoup ((urlopen (urlReq)).read(), 'html.parser')
    subtitleList = dataDiv.find_all ('td', attrs={'class': 'a1'})
    for subtitleLine in subtitleList:
        link = subtitleLine.find ('a')['href']
        for spanNode in subtitleLine.find_all ('span'):
            if spanNode.get('class'):
                rating = spanNode['class']
                language = (spanNode.text).strip()
            else:
                title = spanNode.text

        if not(language in list(subtitleDict.keys())):
            subtitleDict[language] = dict ()
            subtitleDict[language]['count'] = 0

        subtitleDict[language]['count'] += 1
        index = str(subtitleDict[language]['count'])
        subtitleDict[language][index] = dict ()
        subtitleDict[language][index]['title'] = title.strip()
        subtitleDict[language][index]['link'] = link.strip()
        subtitleDict[language][index]['rating'] = ' '.join (rating)

    return subtitleDict

def selectUserLanguage (subtitleDict):
    print (' Select Language:')
    validLanguages = list (subtitleDict.keys())
    for language in sorted(validLanguages):
        print ('   %s' % (language))

    if len (validLanguages) == 0:
        return None

    if 'English' in validLanguages:
        defLanguage = 'English'
    else:
        defLanguage = validLanguages[0]

    while True:
        userLanguage = input(' Select language: [%s] ' % defLanguage) or defLanguage
        if userLanguage.lower() in (temLang.lower() for temLang in validLanguages):
            break

    return userLanguage

def displayAvailableFiles (subtitleDict, userLanguage):
    totalSubtitleCount = subtitleDict[userLanguage]['count']
    sortedIndexKeys = []
    for sno in sorted(list(subtitleDict[userLanguage].keys()), key=lambda item: (int(item.partition(' ')[0]) if item[0].isdigit() else float('inf'), item)):
        if sno == 'count':
            continue
        sortedIndexKeys.append (sno)

    currPage = 1
    displayLen = 20
    promptStr  = '\n Enter number [or] (A)uto search / (P)rev / (N)ext page / e(X)it: '
    promptStrLen = len(promptStr)
    totalPageReq = ceil (totalSubtitleCount / displayLen)
    while True:
        clearScreen ()
        print ('\n\n')
        print ('  ##############################################################')
        print ('        Subtitle Count: %s,  Page %2d / %d' % (totalSubtitleCount, currPage, totalPageReq))
        print ('  ##############################################################')
        startIndex = ((currPage - 1) * displayLen) + 1
        endIndex   = (currPage * displayLen)
        temIndex   = startIndex

        while temIndex <= endIndex and temIndex <= totalSubtitleCount:
            fileRating = getFileRating (subtitleDict[userLanguage][str(temIndex)]['rating'])
            print ('    [ %2s ] [ %2s ] %s' % (temIndex, fileRating, subtitleDict[userLanguage][str(temIndex)]['title']))
            temIndex += 1

        userInput = input (promptStr).strip()
        if userInput.isnumeric() and int(userInput) >= startIndex and int(userInput) <= endIndex:
            downloadSubtitleFile (subtitleDict[userLanguage][userInput]['link'])
            input ('Press enter to continue..')
        elif userInput.lower() == 'a':
            autoSearchAndDownload (subtitleDict[userLanguage])
        elif userInput.lower() == 'n' and currPage < totalPageReq:
            currPage += 1
        elif userInput.lower() == 'p' and currPage > 1:
            currPage -= 1
        elif userInput.lower() == 'x':
            break
    return

def downloadSubtitleFile (link):
    global url, header

    zipFileName = 'temp.zip'
    urlReq = request.Request (url + link, headers=header)
    downloadPage = BeautifulSoup ((urlopen (urlReq)).read(), 'html.parser')
    downloadLink = url + downloadPage.find ('a', attrs={'id': 'downloadButton'})['href']

    urlReq = request.Request (downloadLink, headers=header)
    with open(zipFileName, 'wb') as ptr:
        ptr.write (urlopen(urlReq).read())

    zipObj = ZipFile (zipFileName)
    for zipFileMember in zipObj.namelist():
        if os.path.isfile (zipFileMember):
            fileIndex = 1
            fileNamePrefix = '.'.join(zipFileMember.split ('.')[0:-1])
            while True:
                newFileName = '%s(%d).srt' % (fileNamePrefix, fileIndex)
                if os.path.isfile (newFileName):
                    fileIndex += 1
                else:
                    break
            os.rename (zipFileMember, newFileName)

        zipObj.extract (zipFileMember)
        print ('File %s extracted successfuly' % (zipFileMember))

    zipObj.close ()
    os.remove (zipFileName)
    return

def iterateAndDownload (fileNameList, subtitleDictList):
    for videoFileName in fileNameList:
        for sno in (list(subtitleDictList.keys())):
            if sno == 'count':
                continue
            if subtitleDictList[sno]['title'] == videoFileName:
                downloadSubtitleFile (subtitleDictList[sno]['link'])
    return

def autoSearchAndDownload (subtitleDictList):
    global supportedFileExtensions

    videoFileList = []
    filePath = (input ('Enter video path: [\'.\'] ')).strip() or '.'
    for temFile in glob.glob ('%s/*' % (filePath)):
        if temFile.split ('.')[-1] in supportedFileExtensions:
            temFile = temFile.split('/')[-1]
            temFile = temFile.split('\\')[-1]
            videoFileList.append (temFile)

    iterateAndDownload (videoFileList, subtitleDictList)
    fileList = []
    for temFile in videoFileList:
        temFile = '.'.join(temFile.split('.')[0:-1]) 
        fileList.append (temFile)
    iterateAndDownload (fileList, subtitleDictList)

    input ('Press enter to continue..')
    return

##############################
#### Program starts here  ####
##############################

url = 'https://subscene.com'
queryUrl = url + '/subtitles/title?q='
header= { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
          'Accept-Encoding': 'none',
          'Accept-Language': 'en-US,en;q=0.8',
          'Connection': 'keep-alive'}

supportedFileExtensions = ['3gpp', '3gp', 'avi', 'bsf', 'div1', 'div2', 'div3', 'd2v', 'dvr', 'dvx', 'flv', 'f4f', 'gvi', 'hdv', 'hdv1', 'hdv2', 'hdv3', 'mp4', 'mp41', 'mp42', 'mpeg', 'mpg', 'mkv', 'wav', 'wmv', 'wmv1', 'wmv2']

fileName  = None
searchStr = None
language  = 'english'
serialNum = 1
mainSearchOutput = '\n'

if sys.version_info > (3, 0):
    searchStr = (input ('Enter search text: ')).strip()
else:
    searchStr = (raw_input ('Enter search text: ')).strip()

if searchStr == '':
    print ('INFO: Nothing to search. Exiting ..')
    sys.exit (0)

queryUrl += (searchStr.replace (' ', '+')).replace ('.', '+') + '&l='
queryReq  = request.Request (queryUrl, headers=header)

knownResultTypes = ['exact', 'tv-series', 'popular', 'close']
resultDict = dict ()

headingTitle = None
dataDiv = BeautifulSoup ((urlopen (queryReq)).read(), 'html.parser')
dataDiv = dataDiv.find ('div', attrs={'class': 'search-result'})

for tag in dataDiv.find_all(True):
    if tag.name == 'h2':
        headingTitle = (tag.text)
        continue

    if headingTitle.lower() in knownResultTypes:
        if tag.name == 'ul':
            mainSearchOutput += ' ' + headingTitle + '\n'
            headingTags = tag.find_all ('li')
            for liTag in headingTags:
                sno = str(serialNum)
                serialNum += 1
                resultDict[sno] = dict()

                temLink = liTag.find ('a')
                resultDict[sno]['title'] = temLink.text
                resultDict[sno]['titleLink'] = temLink['href']
                subtitleCount = liTag.find ('div', attrs={'class': 'subtle count'})
                if subtitleCount:
                    resultDict[sno]['subtitleCount'] = (subtitleCount.text).strip()
                else:
                    resultDict[sno]['subtitleCount'] = (liTag.find ('span', attrs={'class': 'subtle count'}).text).strip()

                mainSearchOutput += '   [ %s ] %s - %s' % (sno, resultDict[sno]['title'], resultDict[sno]['subtitleCount']) + '\n'

while True:
    clearScreen ()
    print (mainSearchOutput)
    userInput = input ('Enter serial no. / e(X)it: ')
    if userInput.isnumeric () and userInput in list (resultDict.keys()):
        subtitleDict = getSubtitleList (resultDict[userInput])
        userLanguage = selectUserLanguage (subtitleDict)
        if not(userLanguage):
            print ('WARNING: No files to download for %s' % resultDict[userInput])
            break

        displayAvailableFiles (subtitleDict, userLanguage)
    elif userInput.lower() == 'x':
        print ('INFO: Exiting.. Bye !!')
        break

sys.exit (0)

