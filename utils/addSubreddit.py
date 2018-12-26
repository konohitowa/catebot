import argparse

from orator import DatabaseManager
from orator import Model

from models.subreddit import Subreddit
config = {
    'sqlite': {
        'driver': 'sqlite',
        'database': 'catebot.db',
        'prefix': ''
    }
}

db = DatabaseManager(config)
Model.set_connection_resolver(db)

parser = argparse.ArgumentParser(description='Add subreddits')
parser.add_argument('subreddit', nargs='+', help='Name of a subreddit to add')
args = vars(parser.parse_args())

for s in args['subreddit']:
    subreddit = Subreddit()
    subreddit.subreddit = s
    subreddit.isEnabled = True
    subreddit.isSandbox = False
    subreddit.save()
