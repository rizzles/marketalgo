import pika
import tornado.database
from tornado.options import define, options
import time
import uuid


def callback(ch, method, properties, body):
    print " [x] Received %r" % (body,)

define("mysql_user", default="nick", help="database user")
define("mysql_password", default="mohair94", help="database password")
define("host", default="localhost:3306", help="database")
define("database", default="market", help="database name")

db = tornado.database.Connection(
    host=options.host, database=options.database,
    user=options.mysql_user, password=options.mysql_password)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='market')
channel.exchange_declare(exchange='market', type='fanout')

#channel.basic_consume(callback, queue='market', no_ack=True)
#channel.start_consuming()

class TrendFinder(object):
    def __init__(self, symbol):
        self.symbol = symbol
        self.fh = db.query("""SELECT date,open,close,high,low,id from %s order by date"""% self.symbol)
        self.DAYS = 30
        self.TRENDRATE = 70
        self.trianglefound = False
        self.headfound = False
        self.counter = self.DAYS
        self.pot = 30.0
        self.lastDay = self.fh[0]
        self.boolUP = False
        self.boolDOWN = False

        self.p1date = 0
        self.p1high = 0
        self.p1low = 0
        self.p2date = 0
        self.p2high = 0
        self.p2low = 0
        self.p3date = 0
        self.p3high = 0
        self.p3low = 0
        self.p4date = 0
        self.p4high = 0
        self.p4low = 0
        self.p5date = 0
        self.p5high = 0
        self.p5low = 0
        self.p1set = False
        self.p2set = False
        self.p3set = False
        self.p4set = False
        self.p5set = False
        self.diff = 0
        self.diffhigh = 0
        self.difflow = 0
        self.incriment = False
        self.p1arrow = False
        self.p2arrow = False
        self.p3arrow = False
        self.p4arrow = False
        self.p5arrow = False
        self.trendine = False
        self.p13line = False
        self.p24line = False
        self.nodata = False
        self.daysoftrend = 0
        self.maxdays = 10

    def reset_trend(self):
        self.trianglefound = False
        self.headfound = False
        self.boolUP = False
        self.boolDOWN = False
        self.p1date = 0
        self.p1high = 0
        self.p1low = 0
        self.p2date = 0
        self.p2high = 0
        self.p2low = 0
        self.p3date = 0
        self.p3high = 0
        self.p3low = 0
        self.p4date = 0
        self.p4high = 0
        self.p4low = 0
        self.p5date = 0
        self.p5high = 0
        self.p5low = 0
        self.p1set = False
        self.p2set = False
        self.p3set = False
        self.p4set = False
        self.p5set = False
        self.diff = 0
        self.diffhigh = 0
        self.difflow = 0
        self.incriment = False
        self.p1arrow = False
        self.p2arrow = False
        self.p3arrow = False
        self.p4arrow = False
        self.p5arrow = False
        self.trendline = True
        self.p13line = False
        self.p24line = False
        self.nodata = False
        self.daysoftrend = 0

    def identify_trend(self):
        self.reset_trend()
        # Check to start over
        if self.counter == len(self.fh):
            self.counter = self.DAYS

        """"
        Will be the block that needs changing 
        when algorithim get decided
        """

#        print "Identifying trend for %s"% self.symbol
        up = 0
        down = 0
        # data in fh - date, open, close, high, low
        for row in range(self.counter-(self.DAYS), self.counter):
            # This is the original. Test to see if close is higher than day before
            if self.fh[row]['close'] > self.fh[row-1]['close']:

            # New version. Test to see if close is higher than the first day
#            if self.fh[row]['close'] > self.fh[self.counter-(self.DAYS)]['close']:
                up += 1
            else:
                down += 1

        changeUP = up/self.pot
        changeUP = changeUP * 100
        changeDOWN = down/self.pot
        changeDOWN = changeDOWN * 100

        print "UP",changeUP
        print "DOWN",changeDOWN

        self.p1date = self.fh[self.counter-1]['date']
        self.p1high = self.fh[self.counter-1]['high']
        self.p1low = self.fh[self.counter-1]['low']
        self.p2low = self.p1low
        self.p2high = self.p1high

        if changeUP > self.TRENDRATE and not self.boolUP:
            print 'Upward trend identified for %s. Point 1 set at %.2f'% (self.symbol, self.fh[self.counter]['high'])
            self.boolUP = True
            self.boolDOWN = False
            self.trendline = False
            self.p1arrow = True
            self.p1set = True
            return True
        elif changeDOWN > self.TRENDRATE and not self.boolDOWN:
            print 'Downward trend identified for %s. Point 1 set at %.2f'% (self.symbol, self.fh[self.counter]['low'])
            self.trendline = False
            self.p1arrow = True
            self.boolUP = False
            self.boolDOWN = True
            self.p1set = True
            return True

#        print 'No trend identified'
        return False

class Triangle(object):
    def __init__(self, trendfinder):
        self.symbol = trendfinder.symbol
        self.fh = trendfinder.fh
        self.DAYS = trendfinder.DAYS
        self.TRENDRATE = trendfinder.TRENDRATE
        self.trianglefound = trendfinder.trianglefound
        self.headfound = trendfinder.headfound
        self.counter = trendfinder.counter
        self.pot = trendfinder.pot
        self.lastDay = trendfinder.lastDay
        self.boolUP = trendfinder.boolUP
        self.boolDOWN = trendfinder.boolDOWN

        self.p1date = trendfinder.p1date
        self.p1high = trendfinder.p1high
        self.p1low = trendfinder.p1low
        self.p2date = trendfinder.p2date
        self.p2high = trendfinder.p2high
        self.p2low = trendfinder.p2low
        self.p3date = trendfinder.p3date
        self.p3high = trendfinder.p3high
        self.p3low = trendfinder.p3low
        self.p4date = trendfinder.p4date
        self.p4high = trendfinder.p4high
        self.p4low = trendfinder.p4low
        self.p5date = trendfinder.p5date
        self.p5high = trendfinder.p5high
        self.p5low = trendfinder.p5low
        self.p1set = trendfinder.p1set
        self.p2set = trendfinder.p2set
        self.p3set = trendfinder.p3set
        self.p4set = trendfinder.p4set
        self.p5set = trendfinder.p5set
        self.diff = trendfinder.diff
        self.diffhigh = trendfinder.diffhigh
        self.difflow = trendfinder.difflow
        self.p1arrow = trendfinder.p1arrow
        self.p2arrow = trendfinder.p2arrow
        self.p3arrow = trendfinder.p3arrow
        self.p4arrow = trendfinder.p4arrow
        self.p5arrow = trendfinder.p5arrow
        self.trendline = trendfinder.trendline
        self.p13line = trendfinder.p13line
        self.p24line = trendfinder.p24line
        self.nodata = trendfinder.nodata
        self.daysoftrend = trendfinder.daysoftrend
        self.maxdays = trendfinder.maxdays

    def trend(self):
        # Do check to see if we have data
        if self.counter == len(self.fh):
            return False

        currentDate = self.fh[self.counter]['date']        
        currentClose = self.fh[self.counter]['close']
        currentHigh = self.fh[self.counter]['high']
        currentLow = self.fh[self.counter]['low']

        self.daysoftrend += 1

        if self.daysoftrend >= self.maxdays:
            print "Error", "Trend exceded maximum number of days"
            return False

        # Triangle with a upward trend
        if self.boolUP:
            # Add check into break out of loop if excede max number of days
            if currentHigh > self.p1high:
                self.p2low = self.p1low
                self.boolDOWN = False
                self.boolUP = False
                self.incriment = False
                self.trendline = True
                self.p1arrow = False
                self.p2arrow = False
                self.p3arrow = False
                self.p4arrow = False
                self.p13line = False
                self.p24line = False
                self.p1set = False
                self.p2set = False
                self.p3set = False
                self.p4set = False
                self.p3high = 0
                self.p4low = 0
#                print 'New data is higher than Point 1. Starting to look for new trend.'
                return False
            elif currentLow < self.p1low and currentLow < self.p2low:
                self.p2date = currentDate
                self.p2low = currentLow
                self.diff = self.p1high - self.p2low
                self.diff = self.diff / 3
                self.diffhigh = self.p1high - self.diff
                self.difflow = self.p2low + self.diff
                self.incriment = True
                self.p2arrow = True
                self.p3arrow = False
                self.p13line = False
                self.p2set = True
                self.p3set = False
                self.p4set = False
                self.daysoftrend = 0
#                print 'Point 2 set at %.2f'%self.p2low
            elif self.p2low < self.p1low and currentHigh > self.diffhigh and currentHigh > self.p3high:
                self.p3date = currentDate
                self.incriment = True
                self.p3high = currentHigh
                self.p4low = currentLow
                self.p3arrow = True
                self.p13line = True
                self.p3set = True
                self.p4set = False
                self.daysoftrend = 0
#                print 'Point 3 set at %.2f'%self.p3high
            elif self.p2set and self.p3set and currentLow < self.difflow and currentLow < self.p4low:
                self.p4date = currentDate
                self.p4low = currentLow
                self.p4arrow = True
                self.p24line = True
                self.incriment = False
                self.daysoftrend = 0
#                print 'Point 4 set at %.2f'%self.p4low
                self.trianglefound = True
            else:
#                print 'New data did nothing'
                self.nodata = True

        # Triangle with a downward trend
#        elif self.boolDOWN and self.triangle.isChecked():
        elif self.boolDOWN:
            if currentLow < self.p1low:
                self.p2high = self.p1high
                self.boolDOWN = False
                self.boolUP = False
                self.incriment = False
                self.trendline = True
                self.p1arrow = False
                self.p2arrow = False
                self.p3arrow = False
                self.p4arrow = False
                self.p13line = False
                self.p24line = False
                self.p1set = False
                self.p2set = False
                self.p3set = False
                self.p4set = False
                self.p3low = 0
                self.p4high = 0
#                print 'New data is lower than Point 1. Start looking for new trend.'
            elif currentHigh > self.p1high and currentHigh > self.p2high:
                self.p2date = currentDate
                self.p2high = currentHigh
                self.diff = self.p2high - self.p1low
                self.diff = self.diff / 3
                self.diffhigh = self.p2high - self.diff
                self.difflow = self.p1low + self.diff
                self.incriment = True
                self.p3low = self.difflow
                self.p4high = 0
                self.p2arrow = True
                self.p3arrow = False
                self.p13line = False
                self.p2set = True
                self.p3set = False
                self.p4set = False
                self.daysoftrend = 0
#                print 'Point 2 set at %.2f'%self.p2high
            elif self.p2high > self.p1high and currentLow < self.difflow and currentLow < self.p3low:
                self.p3date = currentDate
                self.incriment = True
                self.p3low = currentLow
                self.p4high = currentHigh
                self.p3arrow = True
                self.p13line = True
                self.p2set = True
                self.p3set = True
                self.p4set = False
                self.daysoftrend = 0
#                print 'Point 3 set at %.2f'%self.p3low
            elif self.p2set and self.p3set and currentHigh > self.diffhigh and currentHigh > self.p4high:
                self.p4date = currentDate
                self.p4high = currentHigh
                self.p4arrow = True
                self.p24line = True
                self.incriment = False
                self.daysoftrend = 0
#                print 'Point 4 set at %.2f'%self.p4high
                self.trianglefound = True               
            else:
#                print 'New data did nothing'
                self.nodata = True
                self.incriment = True

        if self.trianglefound:
            trenduuid = uuid.uuid4()
            trenduuid = trenduuid.hex
            if self.boolDOWN:
                trendtype = "Downward Triangle"
            else:
                trendtype = "Upward Triangle"

            # insert trend in db. send to web server
            db.execute("""INSERT INTO trends(uuid, startdate, date, symbol, type, p1, p2, p3, p4, created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", trenduuid, self.p1date, self.p4date, self.symbol, trendtype, self.p1date, self.p2date, self.p3date, self.p4date, time.time())
            channel.basic_publish(exchange='market', routing_key='', body='%s|%s'% (self.symbol, trenduuid))
            return False

        return True


class HeadAndShoulders(object):
    def __init__(self, trendfinder):
        self.symbol = trendfinder.symbol
        self.fh = trendfinder.fh
        self.DAYS = trendfinder.DAYS
        self.TRENDRATE = trendfinder.TRENDRATE
        self.trianglefound = trendfinder.trianglefound
        self.headfound = trendfinder.headfound
        self.counter = trendfinder.counter
        self.pot = trendfinder.pot
        self.lastDay = trendfinder.lastDay
        self.boolUP = trendfinder.boolUP
        self.boolDOWN = trendfinder.boolDOWN

        self.p1date = trendfinder.p1date
        self.p1high = trendfinder.p1high
        self.p1low = trendfinder.p1low
        self.p2date = trendfinder.p2date
        self.p2high = trendfinder.p2high
        self.p2low = trendfinder.p2low
        self.p3date = trendfinder.p3date
        self.p3high = trendfinder.p3high
        self.p3low = trendfinder.p3low
        self.p4date = trendfinder.p4date
        self.p4high = trendfinder.p4high
        self.p4low = trendfinder.p4low
        self.p5date = trendfinder.p5date
        self.p5high = trendfinder.p5high
        self.p5low = trendfinder.p5low
        self.p1set = trendfinder.p1set
        self.p2set = trendfinder.p2set
        self.p3set = trendfinder.p3set
        self.p4set = trendfinder.p4set
        self.p5set = trendfinder.p5set
        self.diff = trendfinder.diff
        self.diffhigh = trendfinder.diffhigh
        self.difflow = trendfinder.difflow
        self.p1arrow = trendfinder.p1arrow
        self.p2arrow = trendfinder.p2arrow
        self.p3arrow = trendfinder.p3arrow
        self.p4arrow = trendfinder.p4arrow
        self.p5arrow = trendfinder.p5arrow
        self.trendline = trendfinder.trendline
        self.p13line = trendfinder.p13line
        self.p24line = trendfinder.p24line
        self.nodata = trendfinder.nodata
        self.daysoftrend = trendfinder.daysoftrend
        self.maxdays = trendfinder.maxdays

    def trend(self):
        # Do check to see if we have data
        if self.counter == len(self.fh):
            return False

        currentDate = self.fh[self.counter]['date']        
        currentClose = self.fh[self.counter]['close']
        currentHigh = self.fh[self.counter]['high']
        currentLow = self.fh[self.counter]['low']

        if self.daysoftrend >= self.maxdays:
            print "Error", "Trend exceded maximum number of days"
            return False

        # Head and Shoulders trend with an upward trend
        elif self.boolUP:
            # Add check into break out of loop if excede max number of days
            self.daysoftrend += 1
            
            # break out of trend. point 1 is higher
            if currentHigh > self.p1high and not self.p2set:
                self.p2low = self.p1low
                self.boolDOWN = False
                self.boolUP = False
                self.incriment = False
                self.trendline = True
                self.p1arrow = False
                self.p2arrow = False
                self.p3arrow = False
                self.p4arrow = False
                self.p5arrow = False
                self.p13line = False
                self.p24line = False
                self.p1set = False
                self.p2set = False
                self.p3set = False
                self.p4set = False
                self.p5set = False
                self.p3high = 0
                self.p4low = 0
#                print 'New data is higher than Point 1. Start looking for new trend. HeadandShoulders'
                return False
            # Set point 2
            elif currentLow < self.p1low and currentLow < self.p2low and self.p1set and not self.p2set:
                self.p2low = currentLow
                self.p2date = currentDate
                self.diff = self.p1high - self.p2low
                self.diff = self.diff / 3
                self.diffhigh = self.p1high - self.diff
                self.difflow = self.p2low + self.diff
                self.p3high = self.p1high
                self.p2arrow = True
                self.p3arrow = False
                self.p4arrwo = False
                self.p5arrow = False
                self.p2set = True
                self.p3set = False
                self.p4set = False
                self.p5set = False
                self.daysoftrend = 0
                #print 'HEAD Point 2 set at %.2f'% self.p2low
            # Test against point 2 to see if it lower than the current point 2
            elif currentLow < self.p2low and self.p1set and self.p2set and not self.p3set:
                self.p2high = currentHigh
                self.p2low = currentLow
                self.p2date = currentDate
                self.diff = self.p1high - self.p2low
                self.diff = self.diff / 3
                self.diffhigh = self.p1high - self.diff
                self.difflow = self.p2low + self.diff
                self.p3high = self.p1high
                self.p2arrow = True
                self.p3arrow = False
                self.p4arrwo = False
                self.p5arrow = False
                self.p2set = True
                self.p3set = False
                self.p4set = False
                self.p5set = False
                self.daysoftrend = 0
                #print 'HEAD Reset Point 2 set at %.2f'%self.p2low
            # Set point 3
            elif currentHigh > self.p3high and self.p1set and self.p2set and not self.p3set:
                self.p3high = currentHigh
                self.p3date = currentDate
                self.p3arrow = True
                self.p4arrow = False
                self.p5arrow = False
                self.p3set = True
                self.p4set = False
                self.p5set = False
                self.p4low = self.p1high
                self.daysoftrend = 0
                #print 'HEAD Point 3 set at %.2f'%self.p3high
            # Test against point 3 to see if point it higher than the current point 3
            elif currentHigh > self.p3high and self.p1set and self.p2set and self.p3set:
                self.p3high = currentHigh
                self.p3date = currentDate
                self.p3arrow = True
                self.p4arrow = False
                self.p5arrow = False
                self.p3set = True
                self.p4set = False
                self.p5set = False
                self.p24line = False
                self.p4low = self.p1high
                self.daysoftrend = 0
                #print 'HEAD Point 3 set at %.2f'%self.p3high
            # Set point 4
            elif currentLow < self.p4low and self.p1set and self.p2set and self.p3set and not self.p4set:
                self.p4date = currentDate
                self.p4set = True
                self.p4low = currentLow
                self.p24line = True
                self.p4arrow = True
                self.diff = self.p3high - self.p2low
                self.diff = self.diff /2
                self.diffhigh = self.p3high - self.diff
                self.daysoftrend = 0
                #print 'HEAD Point 4 set at %.2f'%self.p4low
            # test against point 4 to see if lower. reset point 4 if it is.
            elif currentLow < self.p4low and self.p1set and self.p2set and self.p3set and self.p4set and not self.p5set:
                self.p4date = currentDate
                self.p4set = True
                self.p5set = False
                self.p4low = currentLow
                self.p4high = currentHigh
                self.p24line = True
                self.p4arrow = True
                self.p5arrow = False
                self.daysoftrend = 0
                #print 'HEAD Reset Point 4 set at %.2f'%self.p4high
            # set new point 5
            elif currentHigh > self.diffhigh and self.p1set and self.p2set and self.p3set and self.p4set and not self.p5set:
                self.p5high = currentHigh
                self.p5set = True
                self.p5date = currentDate
                self.p5arrow = True
                self.daysoftrend = 0
                self.headfound = True               
#                print 'Point 5 set at %.2f'%self.p5high
            else:
                #print 'New data did nothing'
                self.nodata = True
                self.incriment = True

        # Head and shoulders with downward trend
        elif self.boolDOWN:
            # break out of trend. new tick is lower
            if currentLow < self.p1low and not self.p2set:
                self.p2low = self.p1low
                self.boolDOWN = False
                self.boolUP = False
                self.incriment = False
                self.trendline = True
                self.p1arrow = False
                self.p2arrow = False
                self.p3arrow = False
                self.p4arrow = False
                self.p5arrow = False
                self.p13line = False
                self.p24line = False
                self.p1set = False
                self.p2set = False
                self.p3set = False
                self.p4set = False
                self.p5set = False
                self.p3high = 0
                self.p4low = 0
                #print 'New data is lower than Point 1. Start looking for new trend.'
                return False
            # set point 2
            elif currentHigh > self.p1high and currentHigh > self.p2high and self.p1set and not self.p2set:
                self.p2high = currentHigh
                self.p2low = currentLow
                self.p2date = currentDate
                self.diff = self.p1high - self.p2low
                self.diff = self.diff / 3
                self.diffhigh = self.p1high - self.diff
                self.difflow = self.p2low + self.diff
                self.p3low = self.p1low
                self.p4high = self.p4high
                self.p2arrow = True
                self.p3arrow = False
                self.p4arrow = False
                self.p5arrow = False
                self.p2set = True
                self.p3set = False
                self.p4set = False
                self.p5set = False
                self.daysoftrend = 0
                #print 'Point 2 set at %.2f'%self.p2high
            # Test against point 2 to see if it lower than the current point 2
            elif currentHigh > self.p2high and self.p1set and self.p2set and not self.p3set:
                self.p2high = currentHigh
                self.p2low = currentLow
                self.p2date = currentDate
                self.diff = self.p1high - self.p2low
                self.diff = self.diff / 3
                self.diffhigh = self.p1high - self.diff
                self.difflow = self.p2low + self.diff
                self.p3high = self.p1high
                self.p2arrow = True
                self.p3arrow = False
                self.p4arrwo = False
                self.p5arrow = False
                self.p2set = True
                self.p3set = False
                self.p4set = False
                self.p5set = False
                self.daysoftrend = 0
                #print 'HEAD Reset Point 2 set at %.2f'%self.p2low
            # set point 3
            elif currentLow < self.p3low and self.p1set and self.p2set and not self.p3set:
                self.p3high = currentHigh
                self.p3low = currentLow
                self.p3date = currentDate
                self.p3arrow = True
                self.p4arrow = False
                self.p5arrwo = False
                self.p3set = True
                self.p4set = False
                self.p5set = False
                self.p4high = self.p1low
                self.daysoftrend = 0
                #print 'HEAD Point 3 set at %.2f'%self.p3low
            # Test against point 3 to see if point it lower than the current point 3
            elif currentLow < self.p3low and self.p1set and self.p2set and self.p3set:
                self.p3high = currentHigh
                self.p3low = currentLow
                self.p3date = currentDate
                self.p3arrow = True
                self.p4arrow = False
                self.p5arrwo = False
                self.p3set = True
                self.p4set = False
                self.p5set = False
                self.p24line = False
                self.p4high = self.p1low
                self.daysoftrend = 0
                #print 'HEAD Point 3 set at %.2f'%self.p3low)   
            # Set point 4
            elif currentHigh > self.p4high and self.p1set and self.p2set and self.p3set and not self.p4set:
                self.p4date = currentDate
                self.p4set = True
                self.p5set = False
                self.p4low = currentLow
                self.p4high = currentHigh
                self.diff = self.p2high - self.p3low 
                self.diff = self.diff /2
                self.difflow = self.p3low + self.diff
                self.p24line = True
                self.p4arrow = True
                self.p5arrow = False
                self.daysoftrend = 0
                #print 'HEAD Point 4 set at %.2f'%self.p4high
            # test against point 4 to see if higher. reset point 4 if it is.
            elif currentHigh > self.p4high and self.p1set and self.p2set and self.p3set and self.p4set and not self.p5set:
                self.p4date = currentDate
                self.p4set = True
                self.p5set = False
                self.p4low = currentLow
                self.p4high = currentHigh
                self.p24line = True
                self.p4arrow = True
                self.p5arrow = False
                self.daysoftrend = 0
                #print 'HEAD Reset Point 4 set at %.2f'%self.p4high
            # new point 5
            elif currentLow < self.difflow and self.p1set and self.p2set and self.p3set and self.p4set and not self.p5set:
                self.p5high = currentHigh
                self.p5low = currentLow
                self.p5set = True
                self.p5date = currentDate
                self.p5arrow = True
                self.daysoftrend = 0
#                print 'Point 5 set at %.2f'%self.p5low
                self.headfound = True
            else:
                #print 'New data did nothing'
                self.nodata = True
                self.incriment = True 

        if self.headfound:
            trenduuid = uuid.uuid4()
            trenduuid = trenduuid.hex
            if self.boolDOWN:
                trendtype = "Downward Head and Shoulders"
            else:
                trendtype = "Upward Head and Shoulders"

            # insert trend in db. send to web server
            db.execute("""INSERT INTO trends(uuid, startdate, date, symbol, type, p1, p2, p3, p4, p5, created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", trenduuid, self.p1date, self.p5date, self.symbol, trendtype, self.p1date, self.p2date, self.p3date, self.p4date, self.p5date, time.time())
            channel.basic_publish(exchange='market', routing_key='', body='%s|%s'% (self.symbol, trenduuid))
            return False

        return True


watch = []
currentdata = {}
trends = []

sy = db.query("""SHOW TABLES""")
for s in sy:
    watch.append(s['Tables_in_market'])

while True:
    for w in watch:
        print w
        if w == 'trends':
            continue
        if w not in currentdata:
            currentdata[w] = TrendFinder(w)

        if currentdata[w].identify_trend():
            triangle = Triangle(currentdata[w])
            headandshoulders = HeadAndShoulders(currentdata[w])
            trends.append(triangle)
            trends.append(headandshoulders)
#            currentdata[w].counter += 10

        currentdata[w].counter +=1

        for trend in trends:
            res = trend.trend()
            if res == True:
                trend.counter += 1
            else:
                trends.remove(trend)
#        time.sleep(0.1)

    # trim trend database
    numoftrends = db.get("""SELECT count(id) FROM trends""")
    numoftrends = int(numoftrends['count(id)'])
    if numoftrends > 200:
        trim = db.query("""SELECT * FROM trends ORDER BY created desc""")
        for t in trim[200:]:
            db.execute("""DELETE FROM trends WHERE id = %s""", t['id'])
