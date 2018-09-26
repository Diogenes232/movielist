#encoding=utf-8

# Autor: Daniel Abbassi, 2012

import os
import re
import codecs
from os.path import join, getsize

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
    print "Lesefehler ('" + filename + "')."
    return ""
def write_file(filename, data):
    try:
        fileWrite = codecs.open(filename, "w", "utf-8")
        print >> fileWrite, data
        fileWrite.close()
    except:
        fileWrite = codecs.open(filename, "w", "utf-8")
        print >> fileWrite, data
        fileWrite.close()
		
def getCachedIMDbInfo():
    fullCache = read_file("movieCache.txt").splitlines()
    dictAll = {}
    mDict = {}
    
    i=0
    while(i<len(fullCache)):
        line = fullCache[i]
        if (not "[new]" in line and len(line) > 5 and "###" in line):
            attr = line.split("###")[0]
            value = line.split("###")[1].strip()
            mDict[attr] = value
        elif ("[new]" in line):
            dictAll[mDict["this"]] = mDict
            mDict = {}            
        i+=1
    return dictAll
def writeCachedIMDbInfo(dictAll):
    fullCache = []
    
    for movie in dictAll:
        fullCache.append("this###" + movie)
        for el in dictAll[movie]:
            fullCache.append(el + "###" + dictAll[movie][el])
        fullCache.append("[new]")
    
    # Leerzeilen entfernen
    fullCacheNew = []
    for line in fullCache:
        if len(line) > 3:
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
    
    write_file("movieCache.txt", "\r\n".join(fullCache))

##########################################################################################################
# Main
##########################################################################################################

# IMDb-LocalCache abfragen
imdbLocalCache = getCachedIMDbInfo()

# IMDb-LocalCache schreiben
writeCachedIMDbInfo(imdbLocalCache)

wahl = raw_input("\nYa, bitch.")
