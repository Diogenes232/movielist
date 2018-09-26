#encoding=utf-8

# Quelltextgenerierung fuer www.gucknicht.de - Filmographie
# Autor: Daniel Abbassi, 2010

import os
import re
import codecs
from os.path import join, getsize
import movieInfoGrabber #partitiell

rootdirs = movieInfoGrabber.getSetting("movieDirs")
rootdirsDepth = len(rootdirs[0].split("\\"))
templateHtml = movieInfoGrabber.getSetting("templateHtml").replace(r"index.",r"index_2000.")
outputHtml = movieInfoGrabber.getSetting("outputHtmlRoot") + "index_2000.html"

fileExtension_list = ["avi", "mkv", "m4v", "mp4", "mpeg", "mpg", "flv"]
fileExtensionBQ_list = ["mpeg", "mpg", "flv"]
qualityMax = 7

regExp_dubbedLine = re.compile(r'dubbed')
regExp_langDual = re.compile(r'DL')
regExp_langEng = re.compile(r'eng')
regExp_digit = re.compile(r'(\(\d*\))$')
regExp_720p = re.compile(r'(- 720p)$')
regExp_1080p = re.compile(r'(- 1080p)$')
regExp_alphabet = re.compile(r'[A-Za-z]')
regExp_3D = re.compile(r'(0p 3D)$')

#################################################################
# Hilfsfunktionen
#################################################################
def read_file(filename):
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
    print "Lesefehler."
    return ""

def write_file(filename, data):
    fileWrite = codecs.open(filename, "w", "utf-8")
    print >> fileWrite, data
    fileWrite.close()

def writeIfDiffers_file(filename, data):
    data = replaceUmlaute(data)
    try:
        maybeTheSameData = read_file(filename)
        if (not (data in maybeTheSameData)):
            write_file(filename, data)
    except:
        write_file(filename, data)

#################################################################
# Nebenfunktionen
#################################################################

def replaceUmlaute(string):
    return string.replace(r'ä', r'ae').replace(r'ö', r'oe').replace(r'ü', r'ue').replace(r'Ä', r'Ae').replace(r'Ö', r'Oe').replace(r'Ü', r'Ue')
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
            if (l==0) or ( ("unrated" not in part.lower()) and ("uncut" not in part.lower()) and ("director" not in part.lower()) and ("SE" not in part.lower()) and ("extended" not in part.lower()) and ("edition" not in part.lower()) ):
                if (len(name) > 0):
                    name += " - " + part
                else:
                    name = part
            else:
                goOn = False
                
    return name, name2

def getQualityImage(quality):
    # in: quality
    # out: html code for quality
    output = "<table><tr>"
    i=1
    while (i <= qualityMax):
        if (i<=quality):
            output += '<td class="k2"></td>'
        else:
            output += '<td class="k4"></td>'
        i+=1    
    output += '</tr></table>'
    
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
        
##########################################################################################################
# Main
##########################################################################################################

allMovies_dict = {}

# Verzeichnisdaten auslesen
for rootdir in rootdirs:
    for root, dirs, files in os.walk(rootdir):
        for file in files:
            fullFilepath = os.path.join(root, file)
            
            if (getFileSize(getsize(fullFilepath)) > 50):
                movie_dict = {}
                
                if (len(fullFilepath.split("\\")) <= rootdirsDepth+1): # wenn der Film in keinem Unterordner ist (/ wenn keine 2 CDs)
                    
                    movie_dict["fileName"] = ".".join(file.split(r'.')[0:len(file.split(r'.'))-1]) # Endung wird entfernt            
                    movie_dict["fileExtension"] = file.split(r'.')[len(file.split(r'.'))-1].lower() # Endung            
                    movie_dict["fileSize"] = getFileSize(getsize(fullFilepath)) # Groesse
        
                else: # Film mit 2 CDs oder Film-Reihe
                    
                    fileExtension = file.split(r'.')[len(file.split(r'.'))-1].lower()
                    
                    if (fullFilepath.split("\\")[rootdirsDepth] not in allMovies_dict): # Ordnername wird als Filmname genommen, wenn noch nicht verhanden
                        movie_dict["fileName"] = fullFilepath.split("\\")[rootdirsDepth] # Ordnername
                        if (fileExtension in fileExtension_list):
                            movie_dict["fileExtension"] = fileExtension # Endung
                        movie_dict["fileSize"] = getFileSize(getsize(fullFilepath)) # Groesse
                    else:
                        movie_dict = allMovies_dict[fullFilepath.split("\\")[rootdirsDepth]]
                        if (fileExtension in fileExtension_list):
                            movie_dict["fileExtension"] = fileExtension # Endung
                        movie_dict["fileSize"] += getFileSize(getsize(fullFilepath)) # Groesse
                
                allMovies_dict[movie_dict["fileName"]] = movie_dict


######################################################
# zusaetzliche Informationen einholen
for movietag in allMovies_dict:
    movie_dict = allMovies_dict[movietag]
    
    movie_dict["moviename"], movie_dict["movienameLong"] = getMovieNames(movietag)
    
    movie_dict["dubbed"] = hasDubbedLine(movietag)
    movie_dict["numberOfMovies"] = getNumberOfMovies(movietag)
    movie_dict["language"] = getLanguage(movietag)
    
    # Daten in Movie_Dict:
    # fileName / moviename / movienameLong - fileSize / fileExtension / dubbed / numberOfMovies / language
    # + quality
    
    if len(movie_dict["moviename"])<1:
        print movie_dict
        raw_input("Wrong moviename!")

    movie_dict["quality"] = getQuality(movie_dict)    
    allMovies_dict[movietag] = movie_dict
numberOfMovies = len(allMovies_dict)


######################################################
# Sortieren
allMovies_dictSorted = sorted(allMovies_dict, reverse=False)


######################################################
# beim Sortieren die ersten Buchstaben abspeichern für oberste Ankerleiste
lastChar = "-"
htmlfile = read_file(templateHtml)
htmlfile += '<a name="start"> </a>\n<br />\n<table>\n<tr><td>| &nbsp;'
for movietag in allMovies_dictSorted:
    dictionary = allMovies_dict[movietag]
    moviename = dictionary["moviename"]
    
    # Alphabets-Anker werden gesetzt
    if ( re.search(regExp_alphabet,moviename[0]) ):
        firstChar = moviename[0].upper()
    else:
        firstChar = moviename[0]
    if ( re.search(regExp_alphabet,firstChar) and firstChar not in lastChar):
        lastChar = firstChar
        htmlfile += '<a href="#' + firstChar + '">' + firstChar + '</a>&nbsp; |&nbsp; '
htmlfile += "</td></tr>\n</table>\n\n<br />\n\n<table>\n"


######################################################
# Html-Datei erstellen
lastChar = "-"
for movietag in allMovies_dictSorted:
    dict = allMovies_dict[movietag]
    moviename = dict["moviename"]
    movienameLong = dict["movienameLong"]
    
    # Alphabets-Anker werden gesetzt
    if ( re.search(regExp_alphabet,moviename[0]) ):
        firstChar = moviename[0].upper()
    else:
        firstChar = moviename[0]
    if ( re.search(regExp_alphabet,firstChar) and firstChar not in lastChar):
        lastChar = firstChar
        htmlfile += '  <tr><td></td>'
        htmlfile += '<td></td>'
        htmlfile += '<td> <br /><a href="#start"><b>' + firstChar + '</b></a><a name="' + firstChar + '"> </a></td>'
        htmlfile += '<td></td></tr>\n'

    # Filme werden eingefuegt
    htmlfile += '  <tr><td class="imdb"><a href="http://www.imdb.com/find?s=tt&q=' + str(re.sub( r' ', r'+', moviename)) + '" target="_blank">imdb</a></td>'
    htmlfile += '<td class="fs"><a href="http://www.filmstarts.de/suche/?q=' + str(re.sub( r' ', r'+', moviename)) + '" target="_blank">filmstarts</a></td>'
    htmlfile += '<td class="filme">' + movienameLong
    if (dict["numberOfMovies"] > 1):
        htmlfile += ' (' + str(dict["numberOfMovies"]) + ' Teile)'
    htmlfile += ' <font class="lang"> ' + dict["language"] + '</font></td>'
    htmlfile += '<td>' + getQualityImage(dict["quality"]) + '</td></tr>\n'
    htmlfile += '<tr><td class="line"></td><td class="line"></td><td class="line"></td><td class="line"></td><td class="line"></td></tr>\n'

htmlfile += "</table>\n\n</body>\n</html>"

######################################################

print ("write movie_list_2000.. "),
write_file(outputHtml, htmlfile)
print ("ok")

#wahl = raw_input("")