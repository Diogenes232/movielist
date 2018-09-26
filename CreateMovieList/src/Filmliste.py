#encoding=utf-8

# Quelltextgenerierung fuer www.gucknicht.de - Filmographie
# Autor: Daniel Abbassi, 2010

import os, re, xlrd, codecs, urllib3
from os.path import join, getsize

from movieInfoGrabber import *
from BeautifulSoup import BeautifulSoup
from pIMDB import pIMDB

# Parsen Nr. 1
fastMode = False
# Parsen Nr. 2 (wenn fastMode == True)
ignoreUserAsking = False

rootdirs = getSetting("movieDirs")
possibleHDDs = {}
for rd in rootdirs:
    possibleHDDs[rd[0].lower()+":"] = "("+rd[0].upper()+")"

cachedIMDbInfo = getSetting("cachedIMDbInfo")
ownCachedIMDbRating = getSetting("ownCachedIMDbRating")

styleIDs = ["", 2, 3]
outputHtml = getSetting("outputHtml")
outputHtmlRoot = getSetting("outputHtmlRoot")


# IMDb-LocalCache abfragen
imdbLocalCache = getCachedIMDbInfo(cachedIMDbInfo)

# eigenes IMDb-Rating abfragen
myOwnRating = getOwnCachedIMDbRating(ownCachedIMDbRating)

# Verzeichnis durchsuchen
print "walk through dirs\n found: ",
allMovies = walkThroughDirs(rootdirs)
print
    
# aus Tag Details gewinnen (Quali, Sprache, etc.)
print "get additional infos"
allMovies = getAdditionalInfos(allMovies, fastMode, ignoreUserAsking)

# IMDb-LocalCache schreiben
print "write IMDb cache"
writeCachedIMDbInfo(allMovies)

# CoverPics in Quellverzeichnis kopieren
print "create 'copy covers back' file"
copyCoversToDirs(allMovies)

# moegliche Genre auslesen
print "search for genres"
allGenres = getGenres(allMovies)

# HTML-Ausgabe erstellen
print "write index"
allMoviesSorted = sorted(allMovies, reverse=False)
output = giveHtmlList(allMoviesSorted, allMovies, allGenres, possibleHDDs)

# verschiedene Ansichten erstellen
for ID in styleIDs:
    outputCopy = output
    if ID == 2:
        outputCopy = re.sub(regExp_plotEnd, plotInNextLineEnd, re.sub(regExp_plot, plotInNextLine, output))
    writeIfDiffers_file(outputHtml.replace(r'###styleID###', str(ID)), outputCopy.replace(r'###styleID###', str(ID)))

print "write index - sorted by directors,",
# Regisseur-sortierte Ansicht erstellen
allMoviesSortedDirector = sorted(allMovies, reverse=False, key=lambda cand : allMovies[cand]["director"])
output = giveHtmlList( allMoviesSortedDirector, allMovies, allGenres, possibleHDDs ).replace(r'###styleID###', "")
output = output.split("<!--anchor anchor-->")[0] + output.split("<!--anchor anchor-->")[2] # AnchorTable entfernen
writeIfDiffers_file(outputHtmlRoot+"index_Directors.html", output)

print "quality,",
# Dateigroessen-sortierte Ansicht erstellen
allMoviesSortedQuality = sorted(allMovies, reverse=True, key=lambda cand : (allMovies[cand]["fileSize"]/(1.0*max(1,int(allMovies[cand]["numberOfMovies"])))))
output = giveHtmlList( allMoviesSortedQuality, allMovies, allGenres, possibleHDDs ).replace(r'###styleID###', "")
output = output.split("<!--anchor anchor-->")[0] + output.split("<!--anchor anchor-->")[2] # AnchorTable entfernen
writeIfDiffers_file(outputHtmlRoot+"index_Quality.html", output)

print "stereoscopy,",
# 3D-sortierte Ansicht erstellen
allMoviesSortedStereoscopy = sorted(allMovies, reverse=True, key=lambda cand : allMovies[cand]["3D"])
output = giveHtmlList( allMoviesSortedStereoscopy, allMovies, allGenres, possibleHDDs ).replace(r'###styleID###', "")
output = output.split("<!--anchor anchor-->")[0] + output.split("<!--anchor anchor-->")[2] # AnchorTable entfernen
writeIfDiffers_file(outputHtmlRoot+"index_Stereoscopy.html", output)

print "last modification,",
# Datums-basierte Ansicht erstellen
allMoviesSortedLastModificationDate = sorted(allMovies, reverse=True, key=lambda cand : allMovies[cand]["directoryLastModified"])
output = giveHtmlList( allMoviesSortedLastModificationDate, allMovies, allGenres, possibleHDDs ).replace(r'###styleID###', "")
output = output.split("<!--anchor anchor-->")[0] + output.split("<!--anchor anchor-->")[2] # AnchorTable entfernen
writeIfDiffers_file(outputHtmlRoot+"index_LastModificationDate.html", output)

print "my rating,", 
# Eigenwertung-sortierte Ansicht erstellen
for cand in allMovies:
    if not "link" in allMovies[cand] or not giveIMDbID(allMovies[cand]["link"]) in myOwnRating:
        # unbewertete Filme werden in der Mitte angesiedelt
        allMovies[cand]["myRating"] = 5
    else:
        allMovies[cand]["myRating"] = int(myOwnRating[giveIMDbID(allMovies[cand]["link"])])
allMoviesSortedByOwnRating = sorted(allMovies, reverse=True, key=lambda cand : allMovies[cand]["myRating"])
output = giveHtmlList( allMoviesSortedByOwnRating, allMovies, allGenres, possibleHDDs ).replace(r'###styleID###', "")
output = output.split("<!--anchor anchor-->")[0] + output.split("<!--anchor anchor-->")[2] # AnchorTable entfernen
writeIfDiffers_file(outputHtmlRoot+"index_myRating.html", output)

print "IMDb rating"
# Bewertungs-sortierte Ansicht erstellen
for cand in allMovies:
    if not "rating" in allMovies[cand]:
        # unbewertete Filme werden in der Mitte angesiedelt
        allMovies[cand]["rating"] = 5.0
    else:
        try:
            allMovies[cand]["rating"] = float(allMovies[cand]["rating"])
        except:
            allMovies[cand]["rating"] = 5.0
allMoviesSortedImdbRating = sorted(allMovies, reverse=True, key=lambda cand : allMovies[cand]["rating"])
output = giveHtmlList( allMoviesSortedImdbRating, allMovies, allGenres, possibleHDDs ).replace(r'###styleID###', "")
output = output.split("<!--anchor anchor-->")[0] + output.split("<!--anchor anchor-->")[2] # AnchorTable entfernen
writeIfDiffers_file(outputHtmlRoot+"index_IMDbRating.html", output)

# Genre-spezifische Ausgabe
print "write index per genre (",
for oneGenre in allGenres:
    print oneGenre.lower(),
    allVidsSorted, allVids = giveGenreMovies(allMoviesSorted, allMovies, oneGenre)
    output = giveHtmlList( allVidsSorted, allVids, allGenres, possibleHDDs ).replace(r'###styleID###', "")
    writeIfDiffers_file(outputHtmlRoot + "Genre_" + oneGenre + ".html", output)
print ")"

print
print "create millenium list"
os.system("python Filmliste_2000.py")

print "\n", len(allMoviesSorted), "vids.\nnerd."
#wahl = raw_input("")


