import argparse
import sqlite3
import sys
import time

from models.comment import Comment
from orator import DatabaseManager
from orator import Model
from sys import exit

config = {
    'sqlite': {
        'driver': 'sqlite',
        'database': 'catebot.db',
        'prefix': ''
    }
}

db = DatabaseManager(config)
Model.set_connection_resolver(db)

parser = argparse.ArgumentParser(description='Update new database from old')
parser.add_argument('database', help='Database file')
args = vars(parser.parse_args())

# Connects to a sqlite database used to store comment ids.
print('Connecting to database...')
try:
    connection = sqlite3.connect(args['database'])
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    print('Connected to database!')
except:
    print('Connection to database failed.',sys.exc_info()[0])
    exit()

cursor.execute('select id,utc_time from comments where utc_time > ' + str(time.time() - 31*24*60*60))
number = 0
inserts = list()
print("Creating list")
for cid in cursor:
    if (number > 0) and (number % 250) == 0:
        print("Bulk insertion %d" % (number))
        db.table('comments').insert(inserts)
        inserts = list()

    inserts.append({'commentId': cid[0], 'utcTime': cid[1]})
    number += 1

print("Bulk insertion")
db.table('comments').insert(inserts)
