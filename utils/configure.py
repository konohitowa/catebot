import argparse

from orator import DatabaseManager
from orator import Model

from models.configuration import Configuration
config = {
    'sqlite': {
        'driver': 'sqlite',
        'database': 'catebot.db',
        'prefix': ''
    }
}

db = DatabaseManager(config)
Model.set_connection_resolver(db)

parser = argparse.ArgumentParser(description='Catebot configuration')
parser.add_argument('--version', help='Catebot software version', required=True)
parser.add_argument('--username', help='Reddit username', required=True)
parser.add_argument('--password', help='Reddit password', required=True)
parser.add_argument('--clientId', help='Reddit client ID', required=True)
parser.add_argument('--clientSecret', help='Reddit client secret', required=True)
parser.add_argument('--catechismFilename', help='CCC pickle file', required=True)
parser.add_argument('--baltimoreFilename', help='BCCD pickle file', required=True)
parser.add_argument('--canonFilename', help='CCL pickle file', required=True)
parser.add_argument('--girmFilename', help='GIRM pickle file', required=True)
args = vars(parser.parse_args())

configuration = Configuration.find(1)

if not configuration:
    configuration = Configuration()

configuration.version = args['version']
configuration.username = args['username']
configuration.password = args['password']
configuration.clientId = args['clientId']
configuration.clientSecret = args['clientSecret']
configuration.catechismFilename = args['catechismFilename']
configuration.baltimoreFilename = args['baltimoreFilename']
configuration.canonFilename = args['canonFilename']
configuration.girmFilename = args['girmFilename']

configuration.save()
