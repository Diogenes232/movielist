#encoding=utf-8

# Lib zur Erstellung einer Filmliste
# Autor: Daniel Abbassi, 2010

import os, re, xlrd, codecs, time, urllib3, imdbpie, json
from os.path import join, getsize

from BeautifulSoup import BeautifulSoup
from pIMDB import pIMDB

#################################################################
# Konstanten
#################################################################

settingsFile = "settings.txt" #todo : def'd down there again!
#"/my/FilmListe/src/settings.txt"

imdbOnlineLookupCounter = 0

qualityMax = 7
plotLengthMax = 66

http = urllib3.PoolManager()

regExp_dubbedLine = re.compile(r'dubbed')
regExp_langDual = re.compile(r'DL')
regExp_langEng = re.compile(r'eng')
regExp_digit = re.compile(r'(\\(\\d*\\))$')
regExp_720p = re.compile(r'(- 720p)')
regExp_1080p = re.compile(r'(- 1080p)')
regExp_3D = re.compile(r'(0p 3D)$')
regExp_alphabet = re.compile(r'[A-Za-z]')
regExp_plot = re.compile(r'<plotTD>')
regExp_plotEnd = re.compile(r'</plotTD>')

plotInNextLine = '</td><td></td></tr></table>'
plotInNextLine += '<div><plotTD><br />'
plotInNextLineEnd = '<br />&nbsp;</plotTD></div><table><tr><td></td><td></td><td></td><td>'

#################################################################
# Hilfsfunktionen
#################################################################
def read_file(filename):
    datei_IN = False
    try:
        datei_IN = codecs.open(filename, "r", "utf-8")
        return datei_IN.read()
    except:
        pass
    try:
        datei_IN = codecs.open(filename, "r", "iso-8859-1")
        return datei_IN.read()
    except:
        pass
    # the unix way..
    try:
        filenameUnix = changePathToUnixConvention(filename)
        if ( len(filenameUnix) != len(filename) ):
            return read_file( filenameUnix )
    except:
        pass
    
    print "\nLesefehler ('" + filename + "').\n"
    return ""
def changePathToUnixConvention(string):    
    return string.replace(r'\\', '/').replace(r'//', '/')
def write_file(filename, data):
    try:
        fileWrite = codecs.open(filename, "w", "utf-8")
        print >> fileWrite, data
        fileWrite.close()
    except:
        print "\nFehler beim Schreiben der Datei '" + filename + "'.\n"
def substituteTextThatIsNotWriteable(data):
    separationChar = "a"
    
    newData = []
    # print "exception; substituteTextThatIsNotWriteable() ", data, 
    for part in data.split(separationChar):
        try:
            write_file("data\\_testLine.trash", part)
            newData.append(part)
        except:
            #print "\tLINE_WITH_ERROR:", line
            newLine = ""
            for ch in part:
                try:
                    write_file("data\\_testLine.trash", ch)
                    newLine += ch
                except:
                    print " problematic char: ", ch
                    newLine += "_"
            newData.append(newLine)
    #print "all okay.."
    return separationChar.join(newData)
def writeIfDiffers_file(filename, data):
    try:
        maybeTheSameData = read_file(filename)
        if (not (data in maybeTheSameData)):
            write_file(filename, data)
    except:
        try:
            write_file(filename, data)
        except:
            substData = substituteTextThatIsNotWriteable(data)
            write_file(filename, substData)

def getSetting(someStr):
    someStr = str(someStr).strip()
    settings = read_file(settingsFile)
    settingSearched = []
    found = 0
    for line in settings.splitlines():
        line = str(line).strip()

        if found==0 and someStr in line and len(someStr)==len(line):
            found = 1
        elif found==1:
            if len(line) and not (len(line)==1 and "-" in line):
                settingSearched.append(line)
            else:
                found = 2

    if not len(settingSearched):
        print "\nerror - no setting found for input '" + someStr + "'\n"
        return False
    elif len(settingSearched)==1:
        return settingSearched[0]
    else:
        return settingSearched

def getProblematicStringToWork(strWithProblem):
    newThing = []
    print "\tSTRING_WITH_ERROR(getProblematicStringToWork):", strWithProblem
    for line in strWithProblem.split("<tr>"):
        newLine = ""
        for ch in line:
            try:
                write_file("data\\_testLine.trash", ch)
                newLine += str(ch)
            except:
                print ch
                newLine += "_"
        newThing.append( newLine )
    return "<tr>".join(newThing)
def replaceUmlaute(string):
    return string.replace(r'ä', r'ae').replace(r'ö', r'oe').replace(r'ü', r'ue').replace(r'Ä', r'Ae').replace(r'Ö', r'Oe').replace(r'Ü', r'Ue')
def reintegrateUmlaute(string):
    return string.replace(r'ae', r'ä').replace(r'oe', r'ö').replace(r'ue', r'ü').replace(r'Ae', r'Ä').replace(r'Oe', r'Ö').replace(r'Ue', r'Ü')
def giveIMDbID(hyperlink):
    uniqueLinkStr =hyperlink.split("title/tt")[1].split("/")[0]
    uniqueLinkStr = "tt" + str(uniqueLinkStr)
    return uniqueLinkStr

#################################################################
# Verzeichnisse
#################################################################

cachedIMDbInfo = getSetting("cachedIMDbInfo")
ownCachedIMDbRating = getSetting("ownCachedIMDbRating")

print "Loading settings.."
styleIDs = ["", 2, 3]
templateHtml = getSetting("templateHtml")
#print "\t", templateHtml
movieTemplateFile = getSetting("movieTemplateFile")
#print "\t", movieTemplateFile
outputHtml = getSetting("outputHtml")
#print "\t", outputHtml
directoryOfCoverPics = getSetting("directoryOfCoverPics")
#print "\t", directoryOfCoverPics
fileToDistinguishSimilarMovienames = getSetting("fileToDistinguishSimilarMovienames")
#print "\t", directoryOfCoverPics
copyCoversToDirsFile = getSetting("batch_copyCoversToDirsFile")
#print "\t", copyCoversToDirsFile
fileExtension_list = getSetting("fileExtensionsMovies").split()
#print "\t", fileExtension_list
fileExtensionBQ_list = getSetting("fileExtensionsMovies_badQuality").split()
#print "\t", fileExtensionBQ_list
print "..Settings loaded.\n"

#################################################################
# Nebenfunktionen
#################################################################

def getTextInBrackets(text):
    # in: text
    # out: text that is in brackets
    bracketText = ""
    if (len(text.split(" (")) > 1):
        for char in text.split(" (")[1]:
            if (")" not in char):
                bracketText += char
    return bracketText
def getFileSize(sizeInByte):
    # in: size in byte
    # out: size in megabyte
    return int((sizeInByte/1024.0)/1024.0)
def getNumberOfMovies(filetag):
    # in: movie tag
    # out: number of movie, example: (99)
    if ( re.search(regExp_digit, filetag) ):
        return int(getTextInBrackets(filetag))
    else:
        return 1
def hasDubbedLine(tagline):
    # in: movie tag
    # out: if "dubbed" is in the tag
    if ( re.search(regExp_dubbedLine, getTextInBrackets(tagline)) ):
        return True
    else:
        return False
def isIn3D(tagline):
    # in: movie tag
    # out: if "3D" is in the tag
    if ( re.search(regExp_3D, tagline) ):
        return True
    else:
        return False
def getLanguage(tagline):
    # in: movie tag
    # out: language string
    language = "dt"
    if ( re.search(regExp_langDual, getTextInBrackets(tagline)) ):
        language = "dt/eng"
    elif ( re.search(regExp_langEng, getTextInBrackets(tagline)) ):
        language = "eng"
    return language
def getMovieNames(tag):
    # in: movie tag
    # out: filmname mit versionsangabe , filmname ohne rest

    maybeName2 = tag.split(" (")[0]
    name2 = ""
    for part in maybeName2.split(" - "): # "720p/1080p" entfernen
        if ("720p" not in part.lower()) and ("1080p" not in part.lower()):
            if (len(name2) > 0):
                name2 += " - " + part
            else:
                name2 = part

    goOn = True
    name = ""
    l=-1
    for part in name2.split(" - "): # Unnuetzliche Bindestriche entfernen
        l+=1
        if (goOn):
            if (l==0) or ( ("unrated" not in part.lower()) and ("uncut" not in part.lower()) and ("director" not in part.lower()) and ("SE" not in part.lower()) and ("extended" not in part.lower()) and ("edition" not in part.lower()) and ("version" not in part.lower()) ):
                if (len(name) > 0):
                    name += " - " + part
                else:
                    name = part
            else:
                goOn = False

    name = re.sub(r"\.\d{4}\.?", r"", name)
    name2 = re.sub(r"\.\d{4}\.?", r"", name2)
                
    return name, name2

def getQualityImageAndLanguage(quality, lang, thirdDim):
    # in: quality
    # out: html code for quality
    output = '<a href="index_Quality.html"><table><tr><td>Q:</td>'
    
    i=1
    while (i <= qualityMax):
        if (i<=quality):
            output += '<td class="k2"></td>'
        else:
            output += '<td class="k4"></td>'
        i+=1

    output += '<td>'
    if thirdDim: # wenn 3D
        output += '&nbsp;<a href="index_Stereoscopy.html">3D</a>'
    output += '</td><td><font class="lang">(' + lang + ')</font></td></tr></table></a>'
    
    return output
def getQuality(dict):
    # in: movie dict
    # out: 'quality' as integer ( 1 - qualityMax )
    
    # Daten in Movie_Dict:
    # fileName / moviename / movienameLong - fileSize / fileExtension / dubbed / numberOfMovies / language
    
    quality = 1
    size = int(dict["fileSize"]) / int(dict["numberOfMovies"])
    
    if ( re.search(regExp_720p, dict["fileName"]) or re.search(regExp_1080p, dict["fileName"]) ):
        if ( re.search(regExp_720p, dict["fileName"]) ):
            quality = 6
        if ( re.search(regExp_1080p, dict["fileName"]) ):
            quality = 7
    else:
        if (size < 1200):
            quality = 4
        else:
            quality = 5
        if (dict["fileExtension"] in fileExtensionBQ_list):
            quality -= 1
    if (dict["dubbed"]):
        quality -= 1
    
    return quality
def savePicFromUrl(link, mname):
    #print "  loading cover for '" + mname + "' .."
    imgData = http.request('GET', link)
	
    fileName = directoryOfCoverPics + mname.replace(r' ', r'_') + ".jpg"
    output = open(fileName,'wb')
    output.write(imgData.data)
    output.close()
    return mname.replace(r' ', r'_') + ".jpg"
    
def compareNameStringsScore(n1, n2):
    if (n1.lower() in n2.lower() and n2.lower() in n1.lower()):
        return 100
    
    score=0
    name1 = n1.lower().split()
    name2 = n2.lower().split()
    i=0
    for tok in name1:
        tokenRelevance = 100./(0.5*(len(name1)+len(name2))*1.0)
        if (i<len(name2)) and (tok in name2[i] and name2[i] in tok):
            score += tokenRelevance
        elif (i+1<len(name2)) and (tok in name2[i+1] and name2[i+1] in tok):
            score += tokenRelevance * (4./5.)
        elif (i-1>=0 and i-1<len(name2)) and (tok in name2[i-1] and name2[i-1] in tok):
            score += tokenRelevance * (4./5.)
        else:
            if i<len(name2):
                charRelevance = (tokenRelevance * 1.0) / (1.0*len(tok))
                scoreForThatToken = 0
                for ch in tok:
                    if ch in name2[i]:
                        scoreForThatToken += charRelevance
                if (scoreForThatToken >= (3./4.)*tokenRelevance):
                    score += charRelevance
        i+=1
    return score

def getIMDbInfoFromPyIMDb(imdbInfo):
    
    def shortenNameToFitIMDb(name):
        i=0
        newName = ""
        while(len(newName) < len(name)-3):
            newName += name[i]
            i+=1
        return newName
        
    def getRelevantMovieDetails(dict, array):
        for el in array:
            attr = el.split(">>>")[0].lower()
            if "director" in attr:
                dict["director"] = el.split(">>>")[1].strip()
            elif "writer" in attr:
                dict["writer"] = el.split(">>>")[1].split("|")[0].split(", and")[0].split("more credit")[0].strip()
            elif "star" in attr:
                dict["star"] = el.split(">>>")[1].strip()
            elif "tagline" in attr:
                dict["subline"] = el.split(">>>")[1].strip()
            elif "movie duration" in attr:
                dict["duration"] = el.split(">>>")[1].strip().split("min")[0] + "min"
        
        return dict

    def askIMDb(name):
        nameBackup = name
        
        # (1) normale Anfrage
        try:
            imdb = pIMDB(name)
            imdb.parse_imdb_page()
            return imdb
        except:
            pass
        
        # (2) Bindestrich entfernen
        if len(name.split(" -"))>1:
            try:
                imdb = pIMDB(name.split(" -")[0])
                imdb.parse_imdb_page()
                return imdb
            except:
                pass
        
        # (3) Umlaute wieder einfuegen
        try:
            imdb = pIMDB(reintegrateUmlaute(name))
            imdb.parse_imdb_page()
            return imdb
        except:
            pass
        
        # (4) Umlaute entfernen
        try:
            imdb = pIMDB(replaceUmlaute(name))
            imdb.parse_imdb_page()
            return imdb
        except:
            pass
        
        # (5) Name verkuerzen
        while (False and len(name) > 3):
            name = shortenNameToFitIMDb(name)
            try:
                imdb = pIMDB(name)
                imdb.parse_imdb_page()
                return imdb
            except:
                pass
        name = nameBackup
        
        # (6) (Zweiten) Bindestrich entfernen
        if len(name.split(" -"))>1:
            try:
                imdb = pIMDB(name.split(" -")[1].strip())
                imdb.parse_imdb_page()
                return imdb
            except:
                pass
        return False

    moviename = imdbInfo["moviename"]

    # hole von IMDb
    imdbParse = False
    print "  parsing from IMDb: " + moviename,

    imdbParse = askIMDb(moviename)
    
    if not imdbParse:
        print " [movie not found]"
        return imdbInfo
    else:
        print " [success]"
        imdbInfo["link"] = imdbParse.imdb_link
        imdbInfo["name"] = imdbParse.movie
        imdbInfo["rating"] = ("%s/%s" % (imdbParse.rating, imdbParse.outof)).strip().split("/")[0]
        imdbInfo = getRelevantMovieDetails(imdbInfo, imdbParse.details)
        imdbInfo["plot"] = imdbParse.storyline
        try:
            imdbInfo["coverLink"] = savePicFromUrl(imdbParse.posterurl, moviename)
        except:
            pass
        
        imdbLocalCache[moviename] = imdbInfo
        
        return imdbInfo
def getIMDbInfoFromImdbpie(imdbInfo):
    
    def getIMDbDistinction(ia, mName):
        print 
        print 
        print mName
        
        s_result = ia.search_for_title(mName)
        
        html=""
        i=0
        amountPerfectlyMatchingCandidates=0
        lastPerfectlyMatchingCandidate={}
        while(i<min(len(s_result),10)):
            item = s_result[i]
            out = "   ["+str(i)+"] " + (item["title"]) + " (" + str(item["year"]) + ")"
            
            # movie is completely like the searched one
            if (len(item["title"].strip())==len(mName.strip()) and (item["title"].lower().strip() in mName.lower().strip())):
                amountPerfectlyMatchingCandidates += 1
                lastPerfectlyMatchingCandidate = item
            
            s_result[i]["link"] = link = "http://www.imdb.com/title/"+str(item["imdb_id"])
            html += "<br /><a href='"+link+ "' target='_blank'>IMDb</a>&nbsp;&nbsp;&nbsp;" + out
            i+=1
            if(i < 3):
                print out + "\t",
        
        if (amountPerfectlyMatchingCandidates == 1 or len(s_result) == 1):
            return lastPerfectlyMatchingCandidate
        
        print
        oldFile = read_file(fileToDistinguishSimilarMovienames)
        write_file( fileToDistinguishSimilarMovienames, oldFile.split("<center>")[0]+"<center>"+html+"</center>"+oldFile.split("</center>")[1] )
        
        ch = raw_input("  choose your movie (moviesToDistinguish.html or above) number ('n' for new search string): ")
        try:
            if (str(int(ch)) in str(ch) and len(str(int(ch)))==len(ch)):
                return s_result[int(ch)]
        except:
            if (len(ch) > 1):
                return "n"
            else:
                return ch
    
    search = imdbpie.Imdb()
    movieDictShort = -1
    while (("n" in str(movieDictShort) and len(movieDictShort)==1) or movieDictShort==-1):
        if ("n" in str(movieDictShort) and len(movieDictShort)==1):
            bla = raw_input("  name movie string to search for: ")
            movieDictShort = getIMDbDistinction(search, bla)
        else:
            movieDictShort = getIMDbDistinction(search, imdbInfo["moviename"])
    if (not movieDictShort or len(movieDictShort)<3):
        return imdbInfo
    
    imdbInfo["name"] = movieDictShort["title"]
    imdbInfo["year"] = movieDictShort["year"]
    imdbInfo["link"] = movieDictShort["link"]
    imdbInfo["rating"] = ""
    
    #images = search.get_title_images( movieDictShort["imdb_id"] )
    #for im in search._get_images( movieDictShort["imdb_id"] ):
    #    print "Image: ", im
    #if len(images):
    #    imdbInfo["coverLink"] = images[0]
    
    return imdbInfo
def getIMDbInfoFromOMDbApi(imdbInfo):
    # send request
    print "  parsing from OMDb-API '" + imdbInfo["moviename"] + "'",
    link = "http://www.omdbapi.com/?apikey=4cf062d6&i="+imdbInfo["link"].split("title/")[1].split("/")[0]
    answerUntouched = http.request('GET', link)
    
    # parse to JSON
    answer = json.loads(answerUntouched.data)
    
    if "true" in str(answer["Response"]).lower():
        print " [success]"
        imdbInfo["moviename"] = answer["Title"]
        imdbInfo["year"] = answer["Year"]
        imdbInfo["duration"] = answer["Runtime"]
        imdbInfo["genre"] = answer["Genre"].replace(r', ', r' / ')
        imdbInfo["director"] = answer["Director"]
        imdbInfo["writer"] = answer["Writer"]
        imdbInfo["star"] = answer["Actors"]
        imdbInfo["plot"] = answer["Plot"]
        imdbInfo["rating"] = answer["imdbRating"]
        
        if not "coverLink" in imdbInfo:
            try:
                imdbInfo["coverLink"] = savePicFromUrl(answer["Poster"], imdbInfo["moviename"])
            except:
                "Error while saving pic: ", imdbInfo["moviename"], "..", answer["Poster"]
    else:
        print " [failure]"
    
    return imdbInfo
def getIMDbSecondPageInfo(imdb_dict):
    
    def fillWithMoreInfos(info_dict, moreInfo_dictString):
        if len(moreInfo_dictString.split(":"))<2 or "Closed down until further notice" in moreInfo_dictString or '"error"' in moreInfo_dictString.split(":")[1]:
            if "Exceeded API usage limit" in moreInfo_dictString:
                temp = moreInfo_dictString.split("}{")
                if len(temp) < 2:
                    print "  [ ]"
                    return info_dict
                else:
                    moreInfo_dictString = temp[1]
            else:
                print "  [ ]"
                return info_dict
        
        moreInfo_dictStringNew = []
        inValue = False
        tokens = ""
        for t in moreInfo_dictString:
            if '"' in t:
                inValue = not inValue
            elif "," in t and not inValue:
                moreInfo_dictStringNew.append(tokens)
                tokens = ""
            else:
                tokens += t
        
        for el in moreInfo_dictStringNew:
            if ":" in el:
                if "genres" in el.split(":")[0]:
                    info_dict["genre"] = re.search(r':(.*)', el).group(1).replace(r',', r' / ')
                elif "year" in el.split(":")[0]:
                    info_dict["year"] = re.search(r':(.*)', el).group(1)
                # wenn die andere IMDb-Suche nichts ergab
                elif "rating" in el.split(":")[0] and not "rating" in info_dict:
                    info_dict["rating"] = re.search(r':(.*)', el).group(1)
                elif "title" in el.split(":")[0] and not "name" in info_dict:
                    info_dict["name"] = re.search(r':(.*)', el).group(1)
                elif "title" in el.split(":")[0]:
                    info_dict["name2"] = re.search(r':(.*)', el).group(1)
                elif "imdbid" in el.split(":")[0] and not "link" in info_dict:
                    info_dict["link"] = 'http://www.imdb.com/title/' + re.search(r':(.*)', el).group(1)                    
        if "genre" in info_dict or "year" in info_dict:
            print "  [+]"
        else:
            print "  [ ]"
        return info_dict
        
    if "name" in imdb_dict and imdb_dict["name"] in imdb_dict["moviename"]:
        mname = imdb_dict["name"]
    else:
        mname = imdb_dict["moviename"]
    
    if imdb_dict["moviename"] in imdbLocalCache and "year" in imdbLocalCache[imdb_dict["moviename"]]:
        return imdb_dict
    else:
        print "  parsing from IMDb(2): " + mname,
        
        # Suchlink erstellen
        link = "http://www.deanclatworthy.com/imdb/?q=" + mname.replace(r' ', r'+')
        # Suchlink evtl erweitern
        if "link" in imdb_dict and imdb_dict["link"]:
            link += "&id=" + imdb_dict["link"].split("/")[len(imdb_dict["link"].split("/"))-2]
        
        # Suchlink auslesen
        imdb2_dict = "" #urllib2.urlopen(link).read()
        # TODO: old source
        
        # Daten extrahieren
        imdb_dict = fillWithMoreInfos(imdb_dict, imdb2_dict)
    
        return imdb_dict
def getCachedIMDbInfo(fn):
    fullCache = read_file(fn).splitlines()
    dictAll = {}
    mDict = {}
    
    i=0
    while(i<len(fullCache)):
        line = fullCache[i]
        if (not "[new]" in line and len(line) > 5 and "###" in line):
            attr = line.split("###")[0].strip()
            value = line.split("###")[1].strip()
            if "True" in value and len(value)==4:
                value = True
            elif "False" in value and len(value)==5:
                value = False
            if not "isReallyThere" in attr:
                mDict[attr] = value
        elif ("[new]" in line):
            dictAll[mDict["fileName"]] = mDict
            mDict = {}            
        i+=1
    return dictAll
def writeCachedIMDbInfo(dictAll):
    fullCache = []
    
    for movie in dictAll:
        if "isReallyThere" in dictAll[movie]:
            for el in dictAll[movie]:
                if not ("isReallyThere" in str(el) or "this" in str(el)):
                    #print str(el), "->", str(dictAll[movie][el]).strip()
                    try:
                        fullCache.append(str(el) + "###" + str(dictAll[movie][el]).strip())
                    except:
                        fullCache.append( str(el)+"###"+substituteTextThatIsNotWriteable(dictAll[movie][el]).strip() )
            fullCache.append("[new]")
    
    # Leerzeilen entfernen
    fullCacheNew = []
    for line in fullCache:
        if len(line.strip()) > 3:
            fullCacheNew.append(line)
    
    # Doppel-Plot-Zeilen in Cache entfernen
    fullCache = []
    i=-1
    for line in fullCacheNew:
        if len(line) > 3 and not ("###" in line or "[new]" in line) and i>0:
            fullCache[i-1] += line
        elif len(line) > 3: # = "else:"
            i+=1
            fullCache.append(line)
    
    writeIfDiffers_file(cachedIMDbInfo, "\r\n".join(fullCache))
def copyCoversToDirs(movies):
    copyCoversBatch = ""
    for movie in movies:
        movieInfo = movies[movie]
        if "path" in movieInfo and "coverLink" in movieInfo:
            path = movieInfo["path"].split("\\\\")
            path.pop(len(path)-1)
            path = "\\\\".join(path)
            try:
                copyCoversBatch += '\r\nxcopy "' + directoryOfCoverPics + movieInfo["coverLink"] + '" "' + path + '" /Y'
            except:
                pass
            
    write_file(copyCoversToDirsFile, copyCoversBatch)

def getOwnCachedIMDbRating(fn):
    try:
        book = xlrd.open_workbook(fn, encoding_override="cp1252").sheet_by_index(0)
    except:
        return
    
    resultingDict = {}
    
    for rownum in range(1, book.nrows):    
        link = book.row_values(rownum)[0]
        rating = str(int(book.row_values(rownum)[1]))
        resultingDict[link] = rating
    
    return resultingDict

def shortenPlot(plot):
    plot = plot.split()
    shortenedPlot = []
    k=0
    while (k<plotLengthMax and k<len(plot)):
        shortenedPlot.append(plot[k])
        k+=1
    return " ".join(shortenedPlot)
def shortenMovieFact(listOfPeople):
    listOfPeople = listOfPeople.replace(r' and ', r' und ').split("Motion Picture Rating")[0]
    if " und " in listOfPeople and "more credit" in listOfPeople:
        listOfPeople = listOfPeople.split(" und ")[0] + " ..."
    listOfPeople = listOfPeople.split("Season")[0].split("|See full")[0]
    return listOfPeople

def walkThroughDirs(allDirs):
    allMovies_dict = {}
    
    # Verzeichnisdaten auslesen
    for rootdir in allDirs:
        print rootdir
        rootdirsDepth = len(rootdir.split("\\"))
        for root, dirs, files in os.walk(rootdir):
            for file in files:
                fullFilepath = os.path.join(root, file)
                
                if (getFileSize(getsize(fullFilepath)) > 50):
                    movie_dict = {}
                    
                    fileExtension = file.split(r'.')[len(file.split(r'.'))-1].lower()

                    if (fullFilepath.split("\\")[rootdirsDepth] not in allMovies_dict): # Ordnername wird als Filmname genommen, wenn noch nicht verhanden
                        movie_dict["fileName"] = fullFilepath.split("\\")[rootdirsDepth] # Ordnername
                        if (fileExtension in fileExtension_list):
                            movie_dict["fileExtension"] = fileExtension # Endung
                        movie_dict["fileSize"] = getFileSize(getsize(fullFilepath)) # Groesse
                    else:
                        movie_dict = allMovies_dict[fullFilepath.split("\\")[rootdirsDepth]]
                        movie_dict["fileSize"] = movie_dict["fileSize"] + getFileSize(getsize(fullFilepath)) # Groesse
                        
                    if (fileExtension in fileExtension_list):
                        movie_dict["directoryLastModified"] = os.path.getmtime(root)
                    
                    # used to differenciate between movies that are there (on HDD)
                    # and those who WERE there
                    movie_dict["isReallyThere"] = True
                    
                    movie_dict["path"] = fullFilepath
                    allMovies_dict[movie_dict["fileName"]] = movie_dict
                    if (not len(allMovies_dict) % 50):
                        print len(allMovies_dict),
                    
    return allMovies_dict

def getAdditionalInfos(movies_dict, fastMode, ignoreUserAsking):
    
    def itsIdHasEverBeenCorrectlyFound(mDict):
        if "link" in mDict and "tt" in mDict["link"]:
            return True
        return False
    
    def hasBeenEntirelyFoundCorrectly(mDict):
        if not ("coverLink" in mDict):
            return False
        elif ( "coverLink" in mDict and not len(str(mDict["coverLink"])) ):
            return False
        if not ("link" in mDict):
            return False
        elif ("link" in mDict and not "tt" in mDict["link"]):
            return False
        if not ("director" in mDict):
            return False
        elif ( "director" in mDict and not len(str(mDict["coverLink"])) ):
            return False
        return True
    
    for movietag in movies_dict:  # zusaetzliche Informationen einholen
        movie_dict = movies_dict[movietag]
        
        movie_dict["moviename"], movie_dict["movienameLong"] = getMovieNames(movietag)
        
        if len(movie_dict["moviename"])<1:
            print movie_dict
            raw_input("Wrong moviename ('" + movie_dict["moviename"] + "')..")
            
        # get all "old" information
        if movie_dict["fileName"] in imdbLocalCache:
            # additional  
            imdbLocalInfos = imdbLocalCache[movie_dict["fileName"]]
            for fact in imdbLocalInfos:
                if not fact in movie_dict:
                    movie_dict[fact] = imdbLocalInfos[fact]
        
        if itsIdHasEverBeenCorrectlyFound(movie_dict):
            movie_dict["grab"] = 2
        else:
            movie_dict["grab"] = 0
        
        # IMDb-Parse (1)
        if not fastMode and not itsIdHasEverBeenCorrectlyFound(movie_dict):
            movie_dict = getIMDbInfoFromPyIMDb(movie_dict)
            movie_dict["grab"] = 1
            
            if itsIdHasEverBeenCorrectlyFound(movie_dict):
                movie_dict["grab"] = 2
        
            elif not ignoreUserAsking: # IMDb-Parse (2)
                movie_dict = getIMDbInfoFromImdbpie(movie_dict)
                
                if itsIdHasEverBeenCorrectlyFound(movie_dict):
                    movie_dict["grab"] = 2
                    
        if itsIdHasEverBeenCorrectlyFound(movie_dict) and not hasBeenEntirelyFoundCorrectly(movie_dict):
            getIMDbInfoFromOMDbApi(movie_dict)
            
        movie_dict["dubbed"] = hasDubbedLine(movietag)
        movie_dict["numberOfMovies"] = getNumberOfMovies(movietag)
        movie_dict["language"] = getLanguage(movietag)
        movie_dict["3D"] = isIn3D(movietag)
        if not "director" in movie_dict:
            movie_dict["director"] = ""

        movie_dict["quality"] = getQuality(movie_dict)

        movies_dict[movietag] = movie_dict
    return movies_dict

def getGenres(movs):
    genres = {}
    
    for mov in movs:
        mov = movs[mov]
        
        if "genre" in mov and mov["genre"]:
            genresInMovie = mov["genre"].split()            
            for genre in genresInMovie:
                if len(genre) > 2 and genre[0] != genre[0].lower():
                    genres[genre] = genre

    return sorted(genres)
def giveGenreMovies(allMovies_dictSorted, allMovies_dict, genre):
    new_allMovies_dictSorted = []
    new_allMovies_dict = {}
    
    for movietag in allMovies_dictSorted:
        dict = allMovies_dict[movietag]
        
        if "genre" in dict and dict["genre"]:
            if genre in dict["genre"]:
                new_allMovies_dictSorted.append(movietag)
                new_allMovies_dict[movietag] = dict
                
    return new_allMovies_dictSorted, new_allMovies_dict
    
def giveHtmlList(allMovs_dictSorted, allMovs_dict, genreList, possibleHDDs):
    
    def getEmptyPlot(mname):
        text = '<br /><a href="http://www.imdb.com/find?s=tt&q=' + str(re.sub( r' ', r'+', mname)) + '" target="_blank">Suche auf IMDb</a>'
        text += '<br /><a href="http://www.filmstarts.de/suche/?q=' + str(re.sub( r' ', r'+', moviename)) + '" target="_blank">Suche auf Filmstarts.de</a>'
        text += '<br /><a href="http://www.google.de/search?tbm=vid&hl=de&source=hp&q=' + str(re.sub( r' ', r'+', moviename)) + '+trailer" target="_blank"><b>Trailer-Suche (via Google)</b></a><br />&nbsp;'
        return text
    
    def getClickableAnchors(movies):        
        # beim Sortieren die ersten Buchstaben abspeichern für oberste Ankerleiste
        
        lastChar = "-"
        
        anchorTableText = '<a name="start"></a>'
        anchorTableText += '<a href="index.html" target="_parent"><b><inv><normal>&nbsp;Springe zu&nbsp;</inv> <i>(alph. Sortierung)</i></normal></b></a>\n<br />\n'
        anchorTableText += '<!--anchor anchor-->'
        
        anchorTableText += '<table><tr><td><normal>| &nbsp;</normal>'
        for movietag in movies:
            
            moviename = allMovs_dict[movietag]["moviename"]
            if not moviename:
                moviename = allMovs_dict[movietag]["movienameLong"]
            # Alphabets-Anker werden gesetzt                
            if ( re.search(regExp_alphabet,moviename[0]) ):
                firstChar = moviename[0].upper()
            else:
                firstChar = moviename[0]
                
            if ( re.search(regExp_alphabet,firstChar) and firstChar not in lastChar):
                lastChar = firstChar
                anchorTableText += '<a href="#' + firstChar + '"><normal>' + firstChar + '</normal></a><normal>&nbsp; |&nbsp; </normal>'
                
        anchorTableText += '</td></tr>\n</table>'
        anchorTableText += '<!--anchor anchor-->'
        
        return anchorTableText

    def getClickableViewLinks():
        htmlText = '\r\n<table><tr><td><b><inv><normal>&nbsp;Ansicht&nbsp;</inv></normal></b><i><normal> (alle Filme)</i></normal></td></tr></table>'
        htmlText += '\r\n<table><tr>'
        htmlText += '\r\n<td><normal>&nbsp;</normal><a href="index.html"><normal>Standard</normal></a></td>'
        htmlText += '\r\n<td><normal>&nbsp;</normal><a href="index2.html"><normal>Cover</normal></a></td>'
        htmlText += '\r\n<td><normal>&nbsp;</normal><a href="index3.html"><normal>Einfach</normal></a></td>'
        htmlText += '\r\n<td><normal>&nbsp;</normal><a href="index_2000.html"><normal>2000</normal></a></td>'
        htmlText += '\r\n</tr></table>'
        return htmlText

    def getClickableSortLinks():
        htmlText = '\r\n<table><tr>'
        htmlText += '\r\n<td><b><inv><normal>&nbsp;Sortiere nach&nbsp;</inv></normal></b></td>'
        htmlText += '\r\n</tr></table>'
        
        htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        htmlText += '\r\n<a href="index_IMDbRating.html">IMDb-Rating</a>'
        htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        htmlText += '\r\n<a href="index_myRating.html">Eig. Wertung</a>'
        htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        htmlText += '\r\n<a href="index_Stereoscopy.html">Stereoskopie (3D)</a>'
        htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        htmlText += '\r\n<a href="index_Quality.html">Qualit&auml;t</a>'
        htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        htmlText += '\r\n<a href="index_LastModificationDate.html">zuletzt&nbsp;hinzugef&uuml;gt</a>'
        htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        #htmlText += '\r\n<a href="index_Rating5050.html">(Eigene + IMDb-Wertung)</a>'
        #htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        return htmlText

    def getClickableGenreList(genres):
        htmlText = '\r\n<table><tr>'
        htmlText += '\r\n<td><b><inv><normal>&nbsp;Auswahl nach Genre&nbsp;</inv></normal></b></td>'
        htmlText += '\r\n</tr></table>'
        
        htmlText += '\r\n<normal>&nbsp;&nbsp;|&nbsp;&nbsp;</normal>'
        for g in genres:
            htmlText += '\r\n<a href="Genre_' + g + '.html"><normal>' + g + '</normal></a><normal> &nbsp;|&nbsp;&nbsp;</normal>'
        htmlText += '<a href="index.html"><normal><b>alle Filme</b></normal></a><normal>&nbsp;&nbsp;|</normal>'
        return htmlText

    def getOneAnchor(mn, lastCharacter):
        # Alphabets-Anker werden gesetzt
        if ( re.search(regExp_alphabet,mn[0]) ):
            firstChar = mn[0].upper()
        else:
            firstChar = mn[0]        
        if ( re.search(regExp_alphabet,firstChar) and firstChar not in lastCharacter):
            lastCharacter = firstChar
            linkToScrollUp = '<a href="#start"><b>&nbsp;-' + firstChar + '-&nbsp;</b></a><a name="' + firstChar + '"> </a>'
        else:
            linkToScrollUp = ''
        return linkToScrollUp, lastCharacter

    def getSearchLinks(mn):
        htmlText = '\r\n\t\t&nbsp;Suche:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="http://www.filmstarts.de/suche/?q=' + str(re.sub( r' ', r'+', mn)) + '" target="_blank"><font class="search">Filmstarts.de</font></a><br />'
        htmlText += '\r\n\t\t&nbsp;&nbsp;&nbsp;&nbsp;<a href="http://www.google.de/search?tbm=vid&hl=de&source=hp&q=' + str(re.sub( r' ', r'+', mn)) + '+trailer" target="_blank"><font class="search">Trailer(via Google)</font></a>'
        htmlText += '\r\n\t\t&nbsp;&nbsp;&nbsp;<a href="http://www.imdb.com/find?s=tt&q=' + str(re.sub( r' ', r'+', mn)) + '" target="_blank"><font class="search">IMDb</font></a>'
        return htmlText
     
    htmlfileTemplate = read_file(templateHtml)
    
    htmlfile = '<table><tr>\r\n'
    #
    # Anker setzen, har
    htmlfile += '\r\n<td valign="top">'
    htmlfile += getClickableAnchors(allMovs_dictSorted)
    htmlfile += '\r\n</td>'
    #
    htmlfile += '\r\n<td class="viewline"><normal>&nbsp;</normal></td>'
    #
    # Ansicht
    htmlfile += '\r\n<td>'
    htmlfile += getClickableViewLinks()
    #
    htmlfile += '\r\n</td></tr></table>'
    
    # Genre-Auswahl
    htmlfile += getClickableGenreList(genreList)
    htmlfile += '<br />'
    
    # Sortieren nach..
    htmlfile += '\r\n<table><tr><td>'
    htmlfile += getClickableSortLinks()
    htmlfile += '\r\n</td></tr></table>'
    
    htmlfile += '\r\n<hr /><hr /><br />\r\n\r\n'
    
    ######################################################
    # Html-Datei erstellen
    
    movieTemplateBackup = read_file(movieTemplateFile)
    
    lastChar = "-"
    htmlfile += "<table>"
    for movietag in allMovs_dictSorted:
        dict = allMovs_dict[movietag]
        moviename = dict["moviename"]
        movienameLong = dict["movienameLong"]
        if not moviename:
            moviename = movienameLong
        
        # to be edited from now on:
        movieTemplateBackup        
        
        # Cover
        temp = ''
        # Klick auf Cover ermoeglichen
        if "coverLink" in dict and dict["coverLink"]:
            temp += '<a href="covers/' + dict["coverLink"] + '" target="_blank">'
        if "link" in dict and dict["link"]:
            temp += '<img src="'
            if "coverLink" in dict and dict["coverLink"]:
                temp += 'covers/' + dict["coverLink"] + '"'
            else:
                temp += 'covers/bla.jpg"'
            temp += ' class="cover" />'
        if "coverLink" in dict and dict["coverLink"]:
            temp += '</a>'
        movieTemplate = movieTemplateBackup.replace(r'###cover###', temp) # TODO
        
        # Name
        temp = ''
        if "link" in dict and dict["link"]:
            temp += '<a href="' + dict["link"] + '" target="_blank">'
        temp += '<inv>'
        for tok in movienameLong.strip().split():
            temp += '&nbsp;' + tok + '&nbsp; '
        temp += '</inv>'
        if "link" in dict and dict["link"]:
            temp += '</a>'
        # Anzahl der Filme
        if (int(dict["numberOfMovies"]) > 1):
            temp += '&nbsp;(<u>' + str(dict["numberOfMovies"]) + '&nbsp;Teile</u>)'
        try:
            movieTemplate = movieTemplate.replace(r'###moviename###', temp)
        except:
            print dict
            movieTemplate = movieTemplate.replace(r'###moviename###', temp)
        
        # IMDb-Rating und meins!
        temp = ''
        if "rating" in dict and dict["rating"] and len(str(dict["rating"])) <= 3 and int(dict["numberOfMovies"]) < 2 and not ("n" in str(dict["rating"]) and "a" in str(dict["rating"])):
            if "link" in dict and dict["link"]:
                temp += '<a href="' + dict["link"] + 'ratings" target="_blank">'
            temp += '<imdb><b>' + str(dict["rating"]) + '</b>/10</imdb>'
            if "link" in dict and dict["link"]:
                temp += '</a>'
        else:
            temp += '&nbsp;-&nbsp;'
        movieTemplate = movieTemplate.replace(r'###rating###', temp)
        if "link" in dict and giveIMDbID(dict["link"]) in myOwnRating:
            #print giveIMDbID(dict["link"])
            #print myOwnRating[giveIMDbID(dict["link"])]
            temp = '<b>' + myOwnRating[giveIMDbID(dict["link"])] + '</b>/10'
        else:
            temp = '&nbsp;-&nbsp;'
        movieTemplate = movieTemplate.replace(r'###myRating###', temp)

        # Quali und Sprache
        temp = ''
        if "3D" in dict and dict["3D"]:
            in3D = True
        else:
            in3D = False
        temp += getQualityImageAndLanguage(dict["quality"], dict["language"], in3D)
        movieTemplate = movieTemplate.replace(r'###quality###', temp)
        
        # Such-Links
        temp = getSearchLinks(moviename)
        movieTemplate = movieTemplate.replace(r'###searchLinks###', temp)
        
        # Anker zum Regisseur
        temp = ''
        if "director" in dict and dict["director"]:
            dirLink = dict["director"].replace(r' ', r'_')
            temp += '<a name=' + dirLink + '></a>'
        movieTemplate = movieTemplate.replace(r'###directorAnchor###', temp)
        
        # Regisseur(e)
        temp = ''
        if "director" in dict and dict["director"]:
            if "link" in dict and dict["link"]:
                temp += '<a href="' + dict["link"] + 'fullcredits" target="_blank">'
            temp += '<b>' + shortenMovieFact(dict["director"]) + '</b>'
            if "link" in dict and dict["link"]:
                temp += '</a>'
            temp += ' &nbsp;<a href="index_Directors.html#' + dirLink + '">(mehr Filme..)</a>'
        movieTemplate = movieTemplate.replace(r'###director###', temp)
        
        # Autor(en)
        temp = ''
        if "writer" in dict and dict["writer"]:
            if len(dict["writer"].split(","))>1:
                temp += 'en'
        movieTemplate = movieTemplate.replace(r'###Autoren###', temp)        
        temp = ''
        if "writer" in dict and dict["writer"]:
            if "link" in dict and dict["link"]:
                temp += '<a href="' + dict["link"] + 'fullcredits" target="_blank">'
            temp += shortenMovieFact(dict["writer"])
            if "link" in dict and dict["link"]:
                temp += '</a>'
        movieTemplate = movieTemplate.replace(r'###writer###', temp)
        
        # Schauspieler
        temp = ''
        if "star" in dict and dict["star"]:
            if "link" in dict and dict["link"]:
                temp += '<a href="' + dict["link"] + 'fullcredits#cast" target="_blank">'
            temp += shortenMovieFact(dict["star"])
            if "link" in dict and dict["link"]:
                temp += '</a>'
        movieTemplate = movieTemplate.replace(r'###actors###', temp)
        
        # Jahr
        temp = ''
        if "year" in dict and dict["year"]:
            temp += '<i>( ' + dict["year"] + ' )</i>'
        movieTemplate = movieTemplate.replace(r'###year###', temp)
        
        # Tagline
        temp = ''
        if "subline" in dict and dict["subline"]:
            temp += dict["subline"].split("Motion Picture Rating")[0]
        movieTemplate = movieTemplate.replace(r'###tagline###', temp)
            
        # Plot
        temp = ''
        if "plot" in dict and dict["plot"] and len(dict["plot"]) > 5:
            temp += '<br />' + shortenPlot(dict["plot"]) + '... '
            # "geheimes" Zeichen fuer Festplattenkennung
            if "path" in dict and dict["path"]:
                for possibleHDD in possibleHDDs:
                    if possibleHDD in dict["path"].lower():
                        temp += possibleHDDs[possibleHDD]
        else:
            temp += '[find out for yourself]<br />' + getEmptyPlot(movienameLong)
            # "geheimes" Zeichen fuer Festplattenkennung
            if "path" in dict and dict["path"]:
                temp += '<br />'
                for possibleHDD in possibleHDDs:
                    if possibleHDD in dict["path"].lower():
                        temp += possibleHDDs[possibleHDD]
        movieTemplate = movieTemplate.replace(r'###longPlot###', temp)
        
        # Dauer
        temp = ''
        if "duration" in dict and dict["duration"]:
            temp += '<br /><i>Dauer: ' + dict["duration"] + '</i>'
        movieTemplate = movieTemplate.replace(r'###duration###', temp)
        
        # Originaltitel
        temp = ''
        if "name" in dict and dict["name"] and not (dict["name"] in moviename and moviename in dict["name"]) and not "\\\\u" in dict["name"]:
            if ("duration" in dict and dict["duration"]):
                temp += '&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;&nbsp;'
            else:
                temp += '<br />'
            temp += '<i>Originaltitel: ' + dict["name"] + '</i>'
        movieTemplate = movieTemplate.replace(r'###originalName###', temp)
        
        # Genre
        temp = ''
        if "genre" in dict and dict["genre"]:
            temp += '<br /><i>Genre: '
            h=-1
            for genreString in dict["genre"].split("/"):
                genreString = genreString.strip()
                h+=1
                if len(genreString) > 2:
                    temp += '<a href="Genre_' + genreString + '.html">' + genreString + '</a>'
                if h < len(dict["genre"].split("/"))-1:
                    temp += ' / '
            temp += '</i>'
        movieTemplate = movieTemplate.replace(r'###genre###', temp)
        
        # (5) "Anker"
        upScrollLink, lastChar = getOneAnchor(moviename, lastChar)
        temp = upScrollLink
        movieTemplate = movieTemplate.replace(r'###scrollAnchor###', temp)
        
        htmlfile += movieTemplate
        
    htmlfile += "\r\n</table>"
    
    return htmlfileTemplate.replace(r'<!-- insert -->', htmlfile)

##########################################################################################################
# Main
##########################################################################################################

# IMDb-LocalCache abfragen
imdbLocalCache = getCachedIMDbInfo(cachedIMDbInfo)

# eigenes IMDb-Rating abfragen
myOwnRating = getOwnCachedIMDbRating(ownCachedIMDbRating)

