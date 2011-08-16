#! /usr/bin/env python

from xml.dom.minidom import parse, parseString
import urllib2
import time

import MySQLdb

conn = MySQLdb.connect(host="localhost", user="root", passwd="mohair94", db="realtime")
cursor = conn.cursor()


def createtable(symbol):
    cursor.execute("CREATE TABLE %s (id INT AUTO_INCREMENT, querytime INT, lasttradetime INT, open FLOAT, close FLOAT, high FLOAT, low FLOAT, last FLOAT, PRIMARY KEY(id))"% symbol) 


while True:
    req = urllib2.Request('http://app.quotemedia.com/data/getSnapQuotes.xml?symbols=w,c,s,so,sm,ot,us,ty,fy,sp,df,lc,eu,cd,ad,jy&webmasterId=101433')
    response = urllib2.urlopen(req)
    xml = response.read()

    dom = parseString(xml)
    quotes = dom.getElementsByTagName('quote')

    for quote in quotes:
        symbol = quote.firstChild.firstChild.firstChild.data
        cursor.execute("show tables like '%s'"% symbol)
        exists = cursor.fetchone()
        if not exists:
            createtable(symbol)

        o = None
        h = None
        l = None
        c = None
        last = None

        pricedata = quote.getElementsByTagName('pricedata')
        querytime = int(time.time())
        for price in pricedata:
            for data in price.childNodes:
                if data.tagName == 'last':
                    last = data.firstChild.data
                if data.tagName == 'open':
                    o = data.firstChild.data
                if data.tagName == 'high':
                    h = data.firstChild.data
                if data.tagName == 'low':
                    l = data.firstChild.data
                if data.tagName == 'prevclose':
                    c = data.firstChild.data
                if data.tagName == 'lasttradedatetime':
                    lasttrade = time.strptime(data.firstChild.data, "%Y-%m-%dT%H:%M:%S-04:00")
                    lasttrade = time.mktime(lasttrade)
                    # Not sure if time zone data should be taken into effect
#                    lasttrade = lasttrade + 14400

                print data.tagName, data.firstChild.data
            print "------------------------------------------"

            if o and h and l and c and last and lasttrade:
                cursor.execute("INSERT INTO %s(open, high, low, close, last, lasttradetime, querytime) VALUES(%s, %s, %s, %s, %s, %s, %s)"%(symbol, o, h, l, c, last, lasttrade, querytime))

    time.sleep(10)



