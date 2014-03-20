#-----------------------------------------------
# VerseBot for reddit 
# By Matthieu Grieger
# Modified by u/kono_hito_wa
#-----------------------------------------------

import pickle
import configloader
import praw
import sqlite3
from paragraph import Paragraph
from sys import exit
from re import findall
from time import sleep
from os import environ
from warnings import filterwarnings

# Ignores ResourceWarnings when using pickle files. May need to look into this later, but it seems to work fine.
filterwarnings("ignore", category=ResourceWarning)
# Ignores DeprecationWarnings caused by PRAW
filterwarnings("ignore", category=DeprecationWarning) 

print('Starting up Catebot...')

# Loads Bible translation pickle files into memory.
print('Loading Catechism...')
try:
    catechism = pickle.load(open(configloader.getCatechism(), 'rb'))
    print('Catechism successfully loaded!')
except:
    print('Error while loading Catechism. Make sure the environment variable points to the correct path.')
    exit()

# Connects to reddit via PRAW.
print('Connecting to reddit...')
try:
    r = praw.Reddit(user_agent='Catebot by /u/kono_hito_wa. Github: https://github.com/konohitowa/catebot')
    r.login(configloader.getBotUsername(), configloader.getBotPassword())
    print('Connected to reddit!')
except:
    print('Connection to reddit failed. Either reddit is down at the moment, or something in the config is incorrect.')
    exit()


# Connects to a sqlite database used to store comment ids.
print('Connecting to database...')
try:
    conn = sqlite3.connect(configloader.getDatabase())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    print('Connected to database!')
except:
    print('Connection to database failed.')
    exit()

# Fills text file previous comment ids from sqlite database.
print('Setting up tmp.txt...')
try:
    io = open('tmp.txt', 'w')
    cur.execute('select * from commentids')
    rows = cur.fetchall()
    for row in rows:
        io.write(row['comment_id']+'\n')
    io.close()
    print('tmp.txt ready!')
except:
    print('Error when setting up tmp.txt.')
    exit()

commentsAdded = False
nextComment = False
lookupList = list()
timeToWait = 30
comment_ids_this_session = set() # This is to help protect against spamming when connection to database is lost.

print('Beginning to scan comments...')
# This loop runs every 30 seconds.
while True:
    if commentsAdded:
        # Copies new comment ids from database into txt file for searching.
        io = open('tmp.txt', 'w')
        cur.execute('select * from commentids')
        rows = cur.fetchall()
        for row in rows:
            io.write(row['comment_id']+'\n')
        io.close()
    subreddit = r.get_subreddit(configloader.getSubreddits())
    subreddit_comments = subreddit.get_comments()
    try:
        for comment in subreddit_comments:
            if comment.author.name != configloader.getBotUsername() and comment.id not in open('tmp.txt').read() and comment.id not in comment_ids_this_session:
                comment_ids_this_session.add(comment.id)
                paragraphsToFind = findall(r'\[ccc\s*([\d\-,]+)\](?im)', comment.body)
                if len(paragraphsToFind) != 0:
                    for par in paragraphsToFind:
                        lookupList.append(str(par))

                    if len(lookupList) != 0:
                        paragraphObject = Paragraph(lookupList, catechism)
                        # Don't incessantly keep retrying an invalid paragraph
                        if paragraphObject.isValid():
                            nextComment = paragraphObject.getComment()
                            if nextComment != False:
                                try:
                                    comment.reply(nextComment)
                                except praw.errors.RateLimitExceeded:
                                    print("Sleeping 11 minutes due to RateLimitExceed")
                                    sleep(11*60)
                                    comment.reply(nextComment)
                        else:
                            # This has the effect of forcing an insert and then a refresh of tmp.txt
                            nextComment = True

                        paragraphObject.clearParagraphs()
                    else:
                        nextComment = False

                    if nextComment != False:
                        try:
                            cur.execute("INSERT INTO commentids VALUES (?)", (comment.id,))
                            conn.commit()
                        except:
                            print('Database insert failed.')
                            exit()
                        commentsAdded = True
                        lookupList.clear()
                    else:
                        commentsAdded = False
                        try:    
                            # Removes comment id from set if the comment was not replied to. This should prevent situations where the comment
                            # has a valid command and the bot does not reply because the reply operation failed the first time through.
                            comment_ids_this_session.remove(comment.id)
                        except KeyError:
                            pass
                        lookupList.clear()
    
    except requests.exceptions.HTTPError:
        print("HTTP Error: waiting 5 minutes to retry")
        sleep(270) # 300 = 270 + the 30 below
        
    sleep(30)