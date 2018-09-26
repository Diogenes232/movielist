#coding=utf-8

# Autor: Daniel Abbassi
# Beginn: 2012-11

import xlrd
import codecs

def writeFile(filename, data):
    correctlyWritten = False
    try:
        maybeTheSame = codecs.open(filename, "r", "utf-8").read()
        if data in maybeTheSame and len(maybeTheSame)==len(data):
            correctlyWritten = True
    except:
        pass    
    if not correctlyWritten:
        fileWrite = codecs.open(filename, "w", "utf-8")
        print >> fileWrite, data
        fileWrite.close()

book = xlrd.open_workbook("ratings.xls", encoding_override="cp1252").sheet_by_index(0)

result = "<html><head><title></title></head><body><br /><br /><br /><center>"

for rownum in range(book.nrows):
    for el in book.row_values(rownum):
        if len(el.split(",")) > 4:
            result += "&nbsp;&nbsp;&nbsp;&nbsp;"
            name = el.split(",")[5].replace('"', '').strip()
            result += name
            link = el.split(",")[len(el.split(","))-1].replace('"', '').strip()
            result += "&nbsp;&nbsp;&nbsp;&nbsp;"
            result += "<a href='" + link + "' target='_blank'>" + link + "</a>" + "<br /><br />\r\n"
            
result += "<br /></body></html>"
writeFile("rateThis.html", result)