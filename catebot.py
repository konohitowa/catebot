#-----------------------------------------------
# Catebot for reddit 
#  /u/kono_hito_wa
# Originally based upon /u/mgrieger's VerseBot
#-----------------------------------------------

import argparse
import logging
import objects
import pickle
import pprint
import praw
import re
import requests
import sqlite3
import sys
import time

from sys import exit
from time import sleep
from warnings import filterwarnings

# Ignores ResourceWarnings when using pickle files. May need to look into this later, but it seems to work fine.
filterwarnings("ignore", category=ResourceWarning)
# Ignores DeprecationWarnings caused by PRAW
filterwarnings("ignore", category=DeprecationWarning) 

# Configure the logging system
parser = argparse.ArgumentParser(description='Catebot service')
parser.add_argument('-l','--log', help='Log level', required=False)
parser.add_argument('database', help='Database file')
args = vars(parser.parse_args())
if args['log']:
    logLevel = args['log']
else:
    logLevel = 'WARNING'

numeric_level = getattr(logging, logLevel.upper(), logging.WARNING)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
logging.basicConfig(filename='catebot.log', level=numeric_level, format='%(asctime)s:%(levelname)s:%(message)s')

logging.info('Starting up Catebot...')

configuration = objects.Configuration(args['database'])

catechism = pickle.load(open(configuration.getCatechismFilename(), 'rb'))
logging.info('Catechism successfully loaded!')

baltimore = pickle.load(open(configuration.getBaltimoreFilename(), 'rb'))
logging.info('Baltimore Catechism successfully loaded!')

canon = pickle.load(open(configuration.getCanonFilename(), 'rb'))
logging.info('Canon successfully loaded!')

girm = pickle.load(open(configuration.getGIRMFilename(), 'rb'))
logging.info('GIRM successfully loaded!')

try:
    r = praw.Reddit(
        user_agent='Catebot by /u/kono_hito_wa. Github: https://github.com/konohitowa/catebot',
        username=configuration.getUsername(),
        password=configuration.getPassword(),
        client_id=configuration.getClientId(),
        client_secret=configuration.getClientSecret()
        )
    logging.info('Connected to reddit!')
except:
    print('Connection to reddit failed. Either reddit is down at the moment, or something in the config is incorrect.',sys.exc_info()[0])
    logging.critical('Connection to reddit failed. Either reddit is down at the moment, or something in the config is incorrect.',sys.exc_info()[0])
    exit()


# Connects to a sqlite database used to store comment ids.
logging.info('Connecting to database...')
try:
    connection = configuration.getDatabaseConnection()
    cursor = connection.cursor()
    logging.info('Connected to database!')
except:
    print('Connection to database failed.',sys.exc_info()[0])
    logging.critical('Connection to database failed.',sys.exc_info()[0])
    exit()


timeToWait = 30

catechismResponse = objects.Response(catechism, 'http://www.usccb.org/beliefs-and-teachings/what-we-believe/catechism/catechism-of-the-catholic-church/epub/OEBPS/', configuration)
baltimoreResponse = objects.BaltimoreResponse(baltimore, 'http://www.baltimore-catechism.com', configuration)
canonResponse = objects.CanonResponse(canon, 'http://www.vatican.va/archive/ENG1104/', configuration)
girmResponse = objects.GIRMResponse(girm, 'http://www.usccb.org/prayer-and-worship/the-mass/general-instruction-of-the-roman-missal/', configuration)
processedComments = list()
logging.info('Beginning to scan comments...')
# This loop runs every 30 seconds.
while True:
    processedComments.clear()
    cursor.execute('select id from comments')
    for cid in cursor:
        processedComments.append(cid[0])
    subreddit = r.subreddit(configuration.getSubreddits())
    try:
        for comment in subreddit.stream.comments():
            if comment and comment.author.name != configuration.getUsername() and comment.id not in processedComments:
                logging.info("Processing comment %s by user %s" % (comment.id, comment.author.name))
                catechismRequestsToFind = re.findall(r'\[\s*ccc\s*([\d\-,\s]+)\s*\](?im)(?!\()', comment.body)
                if catechismRequestsToFind:
                    requestIsValid,commandResponse = catechismResponse.getResponse(catechismRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                            logging.info("Responded to comment %s by %s" % (comment.id, comment.author.name))
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT": 
                                logging.warning("Sleeping 90 seconds due to RateLimitExceed")
                                sleep(90)
                                comment.reply(commandResponse)
                    
                baltimoreRequestsToFind = re.findall(r'\[\s*bccd\s+(#\d\s+)?([\d\-,\s]+)\s*\](?im)(?!\()', comment.body)
                if baltimoreRequestsToFind:
                    requestIsValid,commandResponse = baltimoreResponse.getResponse(baltimoreRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                            logging.info("Responded to comment %s by %s" % (comment.id, comment.author.name))
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT": 
                                logging.warning("Sleeping 90 seconds due to RateLimitExceed")
                                sleep(90)
                                comment.reply(commandResponse)
                    
                canonRequestsToFind = re.findall(r'\[\s*can\s*([\d\-,s\s]+)\s*\](?im)(?!\()', comment.body)
                if canonRequestsToFind:
                    requestIsValid,commandResponse = canonResponse.getResponse(canonRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT": 
                                logging.warning("Sleeping 90 seconds due to RateLimitExceed")
                                sleep(90)
                                comment.reply(commandResponse)

                girmRequestsToFind = re.findall(r'\[\s*girm\s*([\d\-,\s]+)\s*\](?im)(?!\()', comment.body)
                if girmRequestsToFind:
                    requestIsValid,commandResponse = girmResponse.getResponse(girmRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                        except praw.exceptions.APIException as e:
                            if e.error_type == "RATELIMIT": 
                                logging.warning("Sleeping 90 seconds due to RateLimitExceed ")
                                sleep(90)
                                comment.reply(commandResponse)

                try:
                    cursor.execute("INSERT INTO comments (id,utc_time) VALUES (?,?)", (comment.id, int(time.time())))
                    connection.commit()
                    logging.info("Inserting comment %s by user %s into database" % (comment.id, comment.author.name))
                except:
                    logging.critical("Database insert for comment %s by user %s failed." % (comment.id, comment.author.name),sys.exc_info()[0],"x")
                    exit()
    
    except requests.exceptions.HTTPError:
        logging.error("HTTP Error: waiting 5 minutes to retry"+sys.exc_info()[0],"e")
        sleep(5*60)

