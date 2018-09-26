#encoding=utf-8

# Autor: Daniel Abbassi, 2014

import os, sys
import movieInfoGrabber

rootdirLength = len(movieInfoGrabber.getSetting("movieDirs"))

cachedIMDbInfo = movieInfoGrabber.getSetting("cachedIMDbInfo")
ownCachedIMDbRating = movieInfoGrabber.getSetting("ownCachedIMDbRating")

resultFile = movieInfoGrabber.getSetting("matchesFromWebsearch")
try:
    os.remove( resultFile )
except:
    pass

# IMDb-LocalCache abfragen
imdbLocalCache = movieInfoGrabber.getCachedIMDbInfo(cachedIMDbInfo)
myOwnRating = movieInfoGrabber.getOwnCachedIMDbRating(ownCachedIMDbRating)

# Settings
bestMatchesNumber = 3
try:
    print sys.argv[1]
    giveBestMatchInsteadOfNearestMatches = int(sys.argv[1])
except:
    print "Please call: ' FilmToTomcat_FindMatch.py [0-9](giveBestMatchInsteadOfNearestMatches) FILENAME ' !"
    wahl = raw_input("")
    sys.exit()

stringToFindInFilmnames = ""
i=2
while i < len(sys.argv):
    stringToFindInFilmnames += sys.argv[i] + " "
    i+=1
stringToFindInFilmnames = stringToFindInFilmnames.strip()
print "String to find: '" + stringToFindInFilmnames + "'"

wantedList = []

highestScore_score = 0
highestScore_score_overall = 0
highestScore_moviename = ""
highestScore_moviename_overall = ""
while (len(wantedList)<bestMatchesNumber and not giveBestMatchInsteadOfNearestMatches) or not len(highestScore_moviename_overall):
    highestScore_score = 0
    highestScore_moviename = ""
    for movie in imdbLocalCache:
        name = movie
        movie = imdbLocalCache[movie]
        
        ###################################################################
        name1, name2 = movieInfoGrabber.getMovieNames(name)
        
        compareScore = movieInfoGrabber.compareNameStringsScore(stringToFindInFilmnames, name)*0.25
        compareScore += movieInfoGrabber.compareNameStringsScore(stringToFindInFilmnames, name1)*0.5
        if len(name2) > 0:
            compareScore = compareScore + movieInfoGrabber.compareNameStringsScore(stringToFindInFilmnames, name2)*0.25
        else:
            compareScore = compareScore / 3. * 4.
            
        # new Max found!
        if compareScore > highestScore_score and not name in wantedList:
            highestScore_score = compareScore
            highestScore_moviename = name
            
            # max Max _!min
            if compareScore > highestScore_score_overall:
                highestScore_score_overall = highestScore_score
                highestScore_moviename_overall = highestScore_moviename
        ###################################################################
            
    wantedList.append(highestScore_moviename) 


print "Wanted List: "
for m in wantedList:
    print "\t", m

toWrite = ""
if giveBestMatchInsteadOfNearestMatches:
    toWrite += "\r\n" + imdbLocalCache[highestScore_moviename_overall]["movienameLong"]
    toWrite += "\r\n" + imdbLocalCache[highestScore_moviename_overall]["path"]
    if "coverLink" in imdbLocalCache[highestScore_moviename_overall]:
        toWrite += "\r\n" + imdbLocalCache[highestScore_moviename_overall]["coverLink"]
    if "link" in imdbLocalCache[highestScore_moviename_overall]:
        toWrite += "\r\n" + imdbLocalCache[highestScore_moviename_overall]["link"]
else:
    toWrite = "\r\n".join(wantedList)

print "Writing: " + resultFile
movieInfoGrabber.write_file( resultFile, toWrite.strip() )

print "Done."
