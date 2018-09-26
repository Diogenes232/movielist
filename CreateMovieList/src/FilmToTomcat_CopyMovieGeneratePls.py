#encoding=utf-8

# Autor: Daniel Abbassi, 2014

import os, sys, shutil, time
import movieInfoGrabber

playlistFile_firstLine = "#EXTM3U\r\n#EXTVLCOPT:network-caching=20000\r\n"
playlistFile_someEntry = "#EXTINF:-1,<ENTRYNAME>\r\nhttp://<IP>/f/<FILENAME>\r\n"
hddMapping = {"k":"karl", "l":"lois", "j":"jackson", "n":"nevin"}

# Settings
fileWithDirToCopy = movieInfoGrabber.getSetting("matchesFromWebsearch")
fileExtensionsMovies = movieInfoGrabber.getSetting("fileExtensionsMovies").split()
dirToStoreAndStreamMatches = movieInfoGrabber.getSetting("dirToStoreAndStreamMatches")
currentServerIP = movieInfoGrabber.getSetting("currentServerIP")
notAtest = False
try:
    if(int(sys.argv[1])):
        notAtest = True
    destinationTempDir = sys.argv[2]
except:
    print "Please call: ' FilmToTomcat_CopyMovieGeneratePls.py [0-1]notAtest [0-9](destDirectory) ' !"
    wahl = raw_input("")
    sys.exit()

# readFile that holds the movie's directory
movieInfos = movieInfoGrabber.read_file( fileWithDirToCopy ).strip().splitlines()
try:
    os.remove( fileWithDirToCopy )
except:
    pass
title = movieInfos[0]
if len(movieInfos)>2:
    coverLink = movieInfos[2]
    if len(movieInfos)>3:
        imdbLink = movieInfos[3]

# prepare path
path = movieInfos[1]
path = path.strip().split("\\")
pathCorrectedToUnix = []
pathCorrectedToUnix.append( "/media/" + hddMapping[path[0].split(":")[0].lower()] )
path.pop(len(path)-1)
path.pop(0)
for el in path:
    if len(el):
        pathCorrectedToUnix.append(el)
pathCorrectedToUnix = "/".join(pathCorrectedToUnix)

print "Source path:", pathCorrectedToUnix

#winPath = movieInfos[1].strip().split("\\")
#winPath.pop(len(winPath)-1)
#winPath = "/".join( winPath )
#print winPath

# collect movie files
movieFiles = []
for things in os.walk(pathCorrectedToUnix):
    i=-1
    for info in things:
        i+=1
        if (i==2):
            for fileInDir in info:
                isMovieFile = False
                for extension in fileExtensionsMovies:
                    if (extension in fileInDir and not fileInDir in movieFiles):
                        movieFiles.append(fileInDir)
        elif (i==0):
            filePathSource = info

print "Movie files to copy: "
for mF in movieFiles:
    print "    " + mF

# break before copy
#raw_input("Done!")

# start copy
dirToStoreAndStreamMatches += "/" + destinationTempDir + "/"
playlistFile_content = playlistFile_firstLine
c=1
for movieFile in movieFiles:
    suc = False
    while not suc:
        try:
            fname = "m_" + str(c)
            print "Copy: " + filePathSource + "/" + movieFile + " to: " + dirToStoreAndStreamMatches + fname
            
            # COPY
            if notAtest:
                shutil.copyfile( filePathSource + "/" + movieFile , dirToStoreAndStreamMatches + "m_" + str(c) )
            
            suc = True
            print "Succeded"
            
            playlistFile_content += playlistFile_someEntry.replace(r'<FILENAME>', 'movieTempDir/' + destinationTempDir + '/' + fname)
            playlistFile_content.replace(r'<ENTRYNAME>', fname.replace(r'm', 'Part'))
            #except:
            #    print "\nError while creating playlist file"
        except:
            time.sleep(i*i*2)
            print "\nCopy error! Next try.."
    c+=1
    
playlistFile_content = playlistFile_content.replace(r'<IP>', currentServerIP) # TODO?
movieInfoGrabber.write_file(dirToStoreAndStreamMatches + "vid.m3u8", playlistFile_content)

print "Done."
