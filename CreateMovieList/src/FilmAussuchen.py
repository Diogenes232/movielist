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
    name = movie
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
    #if ratingMoi>=7.0 and "comedy" in genre and ratingIMDb >= 7:
    if ratingIMDb >= 5.6 and "k:" in movie["path"].lower() and "horror" in genre and ratingMoi == 7.5:
        wantedList.append(movie)            
    ###################################################################

print "es stehen " + str(len(wantedList)) + " Filme zur Auswahl:"
for movie in wantedList:
    print movie["moviename"], "\t(",
    if "rating" in movie:
        print movie["rating"], "\t",
        if "link" in movie and giveIMDbID(movie["link"]) in myOwnRating:
            print myOwnRating[giveIMDbID(movie["link"])],
    print ")"
wahl = raw_input("")




