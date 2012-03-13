import tornado.database
from tornado.options import define, options

define("mysql_user", default="nick", help="database user")
define("mysql_password", default="mohair94", help="database password")
define("host", default="localhost:3306", help="database")
define("database", default="realtime", help="database name")

db = tornado.database.Connection(
    host=options.host, database=options.database,
    user=options.mysql_user, password=options.mysql_password)

watch =[]
db.execute("""USE ticks""")
sy = db.query("""SHOW TABLES""")
for s in sy:
    watch.append(s['Tables_in_ticks'])

for x in watch:
    if x[-3:] == 'ten':
        print x
        max = db.get("SELECT max(ID) from %s"% x)
        max = int(max['max(ID)'])
        max = max - 1000
        db.execute("DELETE FROM %s WHERE ID < %s"%(x, max))

    if x[-6:] == 'thirty':
        print x
        max = db.get("SELECT max(ID) from %s"% x)
        max = int(max['max(ID)'])
        max = max - 750
        db.execute("DELETE FROM %s WHERE ID < %s"%(x, max))

    if x[-5:] == 'sixty':
        print x
        max = db.get("SELECT max(ID) from %s"% x)
        max = int(max['max(ID)'])
        max = max - 500
        db.execute("DELETE FROM %s WHERE ID < %s"%(x, max))
