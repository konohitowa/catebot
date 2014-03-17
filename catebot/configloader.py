from os import environ

def getCatechism():
    return environ['CATECHISM']

def getBotUsername():
    return environ['USERNAME']

def getBotPassword():
    return environ['PASSWORD']

def getSubreddits():
    return environ['SUBREDDITS']
    
def getDatabase():
    return environ['DATABASE']