#-----------------------------------------------
# Catebot for reddit 
#  /u/kono_hito_wa
# Originally based upon /u/mgrieger's VerseBot
#-----------------------------------------------

import objects
import pickle
import praw
import re
import sqlite3
import time
import sys
from sys import exit
from time import sleep
from warnings import filterwarnings

# Ignores ResourceWarnings when using pickle files. May need to look into this later, but it seems to work fine.
filterwarnings("ignore", category=ResourceWarning)
# Ignores DeprecationWarnings caused by PRAW
filterwarnings("ignore", category=DeprecationWarning) 

print('Starting up Catebot...')
if len(sys.argv) != 2:
    print("Usage:",sys.argv[0],"<database file>")
    exit(1)

configuration = objects.Configuration(sys.argv[1])

catechism = pickle.load(open(configuration.getCatechismFilename(), 'rb'))
print('Catechism successfully loaded!')

canon = pickle.load(open(configuration.getCanonFilename(), 'rb'))
print('Canon successfully loaded!')

girm = pickle.load(open(configuration.getGIRMFilename(), 'rb'))
print('GIRM successfully loaded!')

try:
    r = praw.Reddit(user_agent='Catebot by /u/kono_hito_wa. Github: https://github.com/konohitowa/catebot')
    r.login(configuration.getUsername(), configuration.getPassword())
    print('Connected to reddit!')
except:
    print('Connection to reddit failed. Either reddit is down at the moment, or something in the config is incorrect.',sys.exc_info()[0])
    exit()


# Connects to a sqlite database used to store comment ids.
print('Connecting to database...')
try:
    connection = configuration.getDatabaseConnection()
    cursor = connection.cursor()
    print('Connected to database!')
except:
    print('Connection to database failed.',sys.exc_info()[0])
    exit()


logger = objects.Logger(configuration.getDatabaseConnection())

timeToWait = 30

catechismResponse = objects.Response(catechism, 'http://www.usccb.org/beliefs-and-teachings/what-we-believe/catechism/catechism-of-the-catholic-church/epub/OEBPS/', configuration)
canonResponse = objects.CanonResponse(canon, 'http://www.vatican.va/archive/ENG1104/', configuration)
girmResponse = objects.GIRMResponse(girm, 'http://www.usccb.org/prayer-and-worship/the-mass/general-instruction-of-the-roman-missal/', configuration)
processedComments = list()
print('Beginning to scan comments...')
# This loop runs every 30 seconds.
while True:
    processedComments.clear()
    cursor.execute('select id from comments')
    for cid in cursor:
        processedComments.append(cid[0])
    subreddit = r.get_subreddit(configuration.getSubreddits())
    subreddit_comments = subreddit.get_comments()
    try:
        for comment in subreddit_comments:
            if comment.author.name != configuration.getUsername() and comment.id not in processedComments:
                catechismRequestsToFind = re.findall(r'\[ccc\s*([\d\-,]+)\](?im)', comment.body)
                if catechismRequestsToFind:
                    requestIsValid,commandResponse = catechismResponse.getResponse(catechismRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                        except praw.errors.RateLimitExceeded:
                            logger.log("Sleeping 11 minutes due to RateLimitExceed"+sys.exc_info()[0])
                            sleep(11*60)
                            comment.reply(commandResponse)
                    
                canonRequestsToFind = re.findall(r'\[can\s*([\d\-,s]+)\](?im)', comment.body)
                if canonRequestsToFind:
                    requestIsValid,commandResponse = canonResponse.getResponse(canonRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                        except praw.errors.RateLimitExceeded:
                            logger.log("Sleeping 11 minutes due to RateLimitExceed"+sys.exc_info()[0])
                            sleep(11*60)
                            comment.reply(commandResponse)

                girmRequestsToFind = re.findall(r'\[girm\s*([\d\-,]+)\](?im)', comment.body)
                if girmRequestsToFind:
                    requestIsValid,commandResponse = girmResponse.getResponse(girmRequestsToFind)
                    if requestIsValid:
                        try:
                            comment.reply(commandResponse)
                        except praw.errors.RateLimitExceeded:
                            logger.log("Sleeping 11 minutes due to RateLimitExceed"+sys.exc_info()[0])
                            sleep(11*60)
                            comment.reply(commandResponse)

                try:
                    cursor.execute("INSERT INTO comments (id,utc_time) VALUES (?,?)", (comment.id, int(time.time())))
                    connection.commit()
                    logger.log(comment.id+","+comment.author.name)
                except:
                    logger.log("Database insert failed."+sys.exc_info()[0],"x")
                    exit()
    
    except requests.exceptions.HTTPError:
        logger.log("HTTP Error: waiting 5 minutes to retry"+sys.exc_info()[0],"e")
        sleep(5*60 - timeToWait)
        
    sleep(timeToWait)