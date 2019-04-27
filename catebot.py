#-----------------------------------------------
# Catebot for reddit
#  /u/kono_hito_wa
# Originally based upon /u/mgrieger's VerseBot
#-----------------------------------------------

import argparse
import logging
import logging.handlers
import objects
import pickle
import pprint
import praw
import re
import requests
import sys
import time

from models.comment import Comment
from models.configuration import Configuration
from models.subreddit import Subreddit
from orator import DatabaseManager
from orator import Model
from sys import exit
from time import sleep
from warnings import filterwarnings

config = {
    'sqlite': {
        'driver': 'sqlite',
        'database': 'catebot.db',
        'prefix': ''
    }
}

db = DatabaseManager(config)
Model.set_connection_resolver(db)

# Ignores ResourceWarnings when using pickle files. May need to look into this later, but it seems to work fine.
filterwarnings("ignore", category=ResourceWarning)
# Ignores DeprecationWarnings caused by PRAW
filterwarnings("ignore", category=DeprecationWarning)

# Configure the logging system
parser = argparse.ArgumentParser(description='Catebot service')
parser.add_argument('-l','--log', help='Log level', required=False)
parser.add_argument('-s','--sandbox', action='store_true', help='Use sandbox subreddit(s) only', required=False)
args = vars(parser.parse_args())
if args['log']:
    logLevel = args['log']
else:
    logLevel = 'WARNING'

numeric_level = getattr(logging, logLevel.upper(), logging.WARNING)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
logging.basicConfig(level=numeric_level, format='%(asctime)s:%(levelname)s:%(message)s')
logger = logging.getLogger('CatebotLogger')
handler = logging.handlers.SysLogHandler(address = '/dev/log')
logger.addHandler(handler)

dblogger = logging.getLogger('orator.connection.queries')
dblogger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    'It took %(elapsed_time)sms to execute the query %(query)s'
)

dbhandler = logging.StreamHandler()
dbhandler.setFormatter(formatter)

dblogger.addHandler(handler)

logger.info('Starting up Catebot...')

configuration = Configuration.find(1)

catechism = pickle.load(open(configuration.catechismFilename, 'rb'))
logger.info('Catechism successfully loaded!')

baltimore = pickle.load(open(configuration.baltimoreFilename, 'rb'))
logger.info('Baltimore Catechism successfully loaded!')

canon = pickle.load(open(configuration.canonFilename, 'rb'))
logger.info('Canon successfully loaded!')

girm = pickle.load(open(configuration.girmFilename, 'rb'))
logger.info('GIRM successfully loaded!')

try:
    r = praw.Reddit(
        user_agent='Catebot by /u/kono_hito_wa. Github: https://github.com/konohitowa/catebot',
        username=configuration.username,
        password=configuration.password,
        client_id=configuration.clientId,
        client_secret=configuration.clientSecret
        )
    logger.info('Connected to reddit!')
except:
    print('Connection to reddit failed. Either reddit is down at the moment, or something in the config is incorrect.',sys.exc_info()[0])
    logger.critical('Connection to reddit failed. Either reddit is down at the moment, or something in the config is incorrect.',sys.exc_info()[0])
    exit()

timeToWait = 30

catechismResponse = objects.Response(catechism, 'http://www.usccb.org/beliefs-and-teachings/what-we-believe/catechism/catechism-of-the-catholic-church/epub/OEBPS/', configuration)
baltimoreResponse = objects.BaltimoreResponse(baltimore, 'http://www.baltimore-catechism.com', configuration)
canonResponse = objects.CanonResponse(canon, 'http://www.vatican.va/archive/ENG1104/', configuration)
girmResponse = objects.GIRMResponse(girm, 'http://www.usccb.org/prayer-and-worship/the-mass/general-instruction-of-the-roman-missal/', configuration)
processedComments = list()
logger.info('Beginning to scan comments...')
# This loop runs every 30 seconds.
while True:
    processedComments.clear()
    for comments in Comment.chunk(1000):
        for comment in comments:
            processedComments.append(comment.commentId)

    subredditFilter = "isEnabled = 1"
    if args['sandbox']:
        subredditFilter += " and isSandbox = 1"
    subredditsList = list()
    for subreddit in Subreddit.where_raw(subredditFilter).get():
        subredditsList.append(subreddit.subreddit)
    subredditQuery = "+".join(subredditsList)
    subreddit = r.subreddit(subredditQuery)
    try:
        for comment in subreddit.stream.comments():
            if comment and comment.author.name != configuration.username and comment.id not in processedComments:
                logger.info("Processing comment %s by user %s" % (comment.id, comment.author.name))
                catechismRequestsToFind = re.findall(r'\[\s*ccc\s*([\d\-,\s]+)\s*\\?\](?im)(?!\()', comment.body)
                if catechismRequestsToFind:
                    requestIsValid,commandResponse = catechismResponse.getResponse(catechismRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                            logger.info("Responded to comment %s by %s" % (comment.id, comment.author.name))
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT":
                                logger.warning("Sleeping 90 seconds due to RateLimitExceed")
                                sleep(90)
                                comment.reply(commandResponse)

                baltimoreRequestsToFind = re.findall(r'\[\s*bccd\s+(#\d\s+)?([\d\-,\s]+)\s*\\?\](?im)(?!\()', comment.body)
                if baltimoreRequestsToFind:
                    requestIsValid,commandResponse = baltimoreResponse.getResponse(baltimoreRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                            logger.info("Responded to comment %s by %s" % (comment.id, comment.author.name))
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT":
                                logger.warning("Sleeping 90 seconds due to RateLimitExceed")
                                sleep(90)
                                comment.reply(commandResponse)

                canonRequestsToFind = re.findall(r'\[\s*can\s*([\d\-,s\s]+)\s*\\?\](?im)(?!\()', comment.body)
                if canonRequestsToFind:
                    requestIsValid,commandResponse = canonResponse.getResponse(canonRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT":
                                logger.warning("Sleeping 90 seconds due to RateLimitExceed")
                                sleep(90)
                                comment.reply(commandResponse)

                girmRequestsToFind = re.findall(r'\[\s*girm\s*([\d\-,\s]+)\s*\\?\](?im)(?!\()', comment.body)
                if girmRequestsToFind:
                    requestIsValid,commandResponse = girmResponse.getResponse(girmRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT":
                                logger.warning("Sleeping 90 seconds due to RateLimitExceed ")
                                sleep(90)
                                comment.reply(commandResponse)

                try:
#                    db.connection().enable_query_log()
                    logger.info("Cleaning database of old comments")
                    db.table('comments').where('utcTime', '<', time.time() - 31*24*60*60).delete()
                    dbComment = Comment()
                    dbComment.commentId = comment.id
                    dbComment.utcTime = time.time()
                    dbComment.save()
                    logger.info("Inserting comment %s by user %s into database" % (comment.id, comment.author.name))
                except:
                    logger.critical("Database insert for comment %s by user %s failed." % (comment.id, comment.author.name),sys.exc_info()[0],"x")
                    exit()

    except requests.exceptions.HTTPError:
        logger.error("HTTP Error: waiting 5 minutes to retry"+sys.exc_info()[0],"e")
        sleep(5*60)
