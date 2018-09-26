#encoding=utf-8

# Autor: Daniel Abbassi, 2012

from pIMDB import pIMDB
import codecs
import os
import re
import urllib2
import xlrd
from movieInfoGrabber import *

rootdirLength = len(getSetting("movieDirs"))

cachedIMDbInfo = getSetting("cachedIMDbInfo")
ownCachedIMDbRating = getSetting("ownCachedIMDbRating")

# IMDb-LocalCache abfragen
imdbLocalCache = getCachedIMDbInfo(cachedIMDbInfo)
myOwnRating = getOwnCachedIMDbRating(ownCachedIMDbRating)

wantedList = []

for movie in imdbLocalCache:    
    movie = imdbLocalCache[movie]
    
    
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
    
    
    if "rating" in movie:
        if "n" in movie["rating"] or "N" in movie["rating"]:
            ratingIMDb = 7.0
        else:
            ratingIMDb = float(movie["rating"])
    else:
        ratingIMDb = 7.0
    
    
    if "link" in movie and giveIMDbID(movie["link"]) in myOwnRating:
        ratingMoi = float(myOwnRating[giveIMDbID(movie["link"])])
    else:
        ratingMoi = 7.5
        
    # A-U-S-D-R-U-C-K  ZUM  F-I-N-D-E-N  EINES  F-I-L-M-S
    quality
    isInHD
    isIn3D
    genre
    ratingIMDb
    ratingMoi
    ###################################################################
    if (ratingMoi<=6.0 and ratingIMDb <= 6.7):
        wantedList.append(movie)            
    ###################################################################

rem = "" #"#!//bin//sh\r\n\r\n"
i=0
for movie in wantedList:
    i+=1
    rem += '\r\nrd /S /Q "' + movie["fileName"] + '"'
    #rem += "\r\nrm -r " + doItTheUnixWay(movie["fileName"]) + "/ -bla"

write_file(getSetting("batch_deleteMoviesFile").replace(".x", ".bat"), rem)
#write_file(getSetting("batch_deleteMoviesFile").replace(".x", ".sh"), rem)
print i, "movies found to delete"
print "done"

