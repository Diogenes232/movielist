#encoding=utf-8

# Autor: Daniel Abbassi, 2012

from pIMDB import pIMDB
import codecs
import os
import re
import urllib2
import xlrd
from movieInfoGrabber import *

syncBatch = getSetting("batch_sync")

syncTargetDir = getSetting("syncTargetDir")
sourceDirs = getSetting("movieDirs")
sourceDirLength = len(sourceDirs)

callAutomatically = False
copyTimePerGB = 0.5

exceptedFromSyncListPath = getSetting("exceptedFromSyncListPath")
cachedIMDbInfo = getSetting("cachedIMDbInfo")
ownCachedIMDbRating = getSetting("ownCachedIMDbRating")

def unlistUnwantedMovies(wanted, moviesAlreadyThere):
    
    doNotSync = read_file(exceptedFromSyncListPath).splitlines()
    doNotSyncList = []
    for dns in doNotSync:
        doNotSyncList.append(dns.strip())    
    
    reallyWanted =  {}
    wholeSize = 0
    
    for m in wanted:
        if not (m["fileName"] in moviesAlreadyThere or m["fileName"] in doNotSyncList):
            wholeSize += int(m["fileSize"])
            reallyWanted[m["fileName"]] = m
    
    newReallyWanted = reallyWanted
    
    choice = " "
    lastMessage = ""
    while len(choice):
        
        reallyWanted = newReallyWanted
        newReallyWanted = {}
        
        print "\n\n\nZu kopierende Filme:\n"    
        for m in wanted:
            if not (m["fileName"] in moviesAlreadyThere or m["fileName"] in doNotSyncList):
                print m["fileName"] + "   (" + str(m["fileSize"]) + "MB)"
        
        if len(lastMessage):
            print
            print lastMessage
        
        print        
        print "Sync-Umfang: " + str(int(wholeSize/1024.0)) + "GB  -  Sync-Dauer etwa " + str(int(wholeSize/1024.0/(copyTimePerGB/1.2))) + "min"
        choice = raw_input("Film aus Synchronisation ausschliessen? ('Enter' zum Verlassen)\n")
        
        i = 0
        oddMovie = ""
        for m in reallyWanted:
            if not choice.lower() in m.lower():
                newReallyWanted[m] = reallyWanted[m]
            else:
                oddMovie = m
                i+=1
        
        if i==0:
            print "Es wurde kein Film entfernt."
            lastMessage = "Es wurde kein Film entfernt."
        elif i > 1 and len(choice):
            print "Filname uneindeutig."
            lastMessage = "Filname uneindeutig."
            newReallyWanted = reallyWanted
        elif i > 1:
            newReallyWanted = reallyWanted
        else:
            doNotSyncList.append(oddMovie)
            print "'" + oddMovie + "' entfernt."
            lastMessage = "'" + oddMovie + "' entfernt."
            for m in wanted:
                if choice.lower() in m["fileName"].lower():
                    wholeSize -= int(m["fileSize"])
    
    write_file(exceptedFromSyncListPath, "\r\n".join(doNotSyncList))
    return reallyWanted

def sync(moviesWanted, moviesAll):
    # alle 3 Uebergaben sind Dicts mit korrekten Dateinamen als Schluessel
    
    out = ""
    
    for m in moviesWanted:
        out += '\r\nmkdir "' + syncTargetDir + '\\' + m + '"'
        out += '\r\nxcopy "' + moviesAll[m]['path'].split('\\')[0] + '\\' + moviesAll[m]['path'].split('\\')[1] + '\\' + moviesAll[m]['path'].split('\\')[2] + '" "'
        out += syncTargetDir + '\\' + m + '" /S /E /I'
        
    write_file(syncBatch, out)

def seeIfMovieIsWanted(cache):
    wantedList = []
    
    for movie in cache:    
        movie = cache[movie]
        
        
        if "3D" in movie:
            isIn3D = movie["3D"]
        else:
            isIn3D = False
        
        
        if "quality" in movie:
            quality = int(movie["quality"])
        else:
            quality = 4
        isInHD = quality > 5
        
        
        if "genre" in movie:
            genre = movie["genre"].lower().split()
        else:
            genre = []
        
        
        if "rating" in movie and len(movie["rating"])<4 and not "N" in movie["rating"]:
            ratingIMDb = float(movie["rating"])
        else:
            ratingIMDb = 7.0
        
        
        if "link" in movie and giveIMDbID(movie["link"]) in myOwnRating:
            ratingMoi = float(myOwnRating[giveIMDbID(movie["link"])])
        else:
            ratingMoi = 7.5
            
        # A-U-S-D-R-U-C-K  ZUM  F-I-N-D-E-N  EINES  F-I-L-M-S
        ###################################################################
        quality
        isInHD
        isIn3D
        genre #(.lower)
        ratingIMDb
        ratingMoi
        ###################################################################
        
        if (ratingMoi < 8.0 and ratingMoi > 7.0 and ratingIMDb > 7.9) and not isIn3D:
            wantedList.append(movie)
            
        ###################################################################
            
    return wantedList

print "get own/IMDb's cache"
imdbLocalCache = getCachedIMDbInfo(cachedIMDbInfo)
myOwnRating = getOwnCachedIMDbRating(ownCachedIMDbRating)

# Sammlungen erstellen
print "walk through directories"
allMovies = walkThroughDirs(sourceDirs)
allMovies_extern = walkThroughDirs( [syncTargetDir] )

print "see what is wanted",
wantedMovies = seeIfMovieIsWanted(imdbLocalCache)

# Sync-Liste anzeigen (und Rausschmiss ermoeglichen)
wantedMovies = unlistUnwantedMovies(wantedMovies, allMovies_extern)

sync(wantedMovies, allMovies)

if callAutomatically:
    os.system(syncBatch)
else:
    choice = raw_input("Nun synchronisieren?\n - 'ok' eingeben zum Starten\n - druecke 'Enter' zum Beenden\n")
    if len(choice) and "ok" in choice:
        os.system(syncBatch)

wahl = raw_input("\nBeendet.")




