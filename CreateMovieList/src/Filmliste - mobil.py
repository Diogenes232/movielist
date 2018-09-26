#encoding=utf-8

# Quelltextgenerierung fuer www.gucknicht.de - Filmographie
# Autor: Daniel Abbassi, 2010

import os
import re
import xlrd
import codecs
from os.path import join, getsize

from movieInfoGrabber import *
from BeautifulSoup import BeautifulSoup
from pIMDB import pIMDB
import urllib3

# kein erneutes Parsen von IMDb
fastMode = True

rootdirs = getSetting("syncTargetDir")
possibleHDDs = {'l:': '..', 'k:': '....'}

cachedIMDbInfo = getSetting("cachedIMDbInfo")
ownCachedIMDbRating = getSetting("ownCachedIMDbRating")

# IMDb-LocalCache abfragen
imdbLocalCache = getCachedIMDbInfo(cachedIMDbInfo)

# eigenes IMDb-Rating abfragen
myOwnRating = getOwnCachedIMDbRating(ownCachedIMDbRating)

# Verzeichnis durchsuchen
print "walk through dirs"
allMovies = walkThroughDirs(rootdirs)
print len(allMovies), "movies found"
    
# aus Tag Details gewinnen (Quali, Sprache, etc.)
print "get additional infos"
allMovies = getAdditionalInfos(allMovies, fastMode, fastMode)

# IMDb-LocalCache schreiben
#print "write IMDb cache"
#writeCachedIMDbInfo(allMovies)

# moegliche Genre auslesen
print "search for genres"
allGenres = getGenres(allMovies)

# HTML-Ausgabe erstellen
print "write index"
allMoviesSorted = sorted(allMovies, reverse=False)
output = giveHtmlList(allMoviesSorted, allMovies, allGenres, possibleHDDs)

#output = re.sub(regExp_plotEnd, plotInNextLineEnd, re.sub(regExp_plot, plotInNextLine, output))
write_file(getSetting("outputHtmlMobile"), output.replace(r'###styleID###', str("")))

print "\n", len(allMoviesSorted), "vids on that thing.\nnerd."
wahl = raw_input("")




