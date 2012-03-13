import tornado.database
from tornado.options import define, options

define("mysql_user", default="nick", help="database user")
define("mysql_password", default="mohair94", help="database password")
define("host", default="localhost:3306", help="database")
define("database", default="realtime", help="database name")

db = tornado.database.Connection(
    host=options.host, database=options.database,
    user=options.mysql_user, password=options.mysql_password)

watch = []


db.execute("""USE realtime""")
sy = db.query("""SHOW TABLES""")
for s in sy:
    watch.append(s['Tables_in_realtime'])

print "realtime table"
for x in watch:
    if x == 'ZWH2':
        table = list(x)
        table[2] = 'K'
        new = "".join(table)
        print x,new
        db.execute("""RENAME TABLE %s TO %s"""%(x, new))


print "ticks table"
db.execute("""USE ticks""")
sy = db.query("""SHOW TABLES""")
for s in sy:
    watch.append(s['Tables_in_ticks'])

for x in watch:
    if x.startswith('ZWH2_'):
        table = list(x)
        table[2] = 'K'
        new = "".join(table)
        print x,new
#        db.execute("""RENAME TABLE %s TO %s"""%(x, new))

