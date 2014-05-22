import re
import sqlite3
import time

class Configuration:
    
    def __init__(self, databaseFilename):
        self._connection = sqlite3.connect(databaseFilename)
        self._connection.row_factory = sqlite3.Row
        cursor = self._connection.cursor()
        cursor.execute("select version,username,password,catechismFilename,canonFilename,girmFilename from configuration")
        row = cursor.fetchone()
        self._version = row[0]
        self._username = row[1]
        self._password = row[2]
        self._catechismFilename = row[3]
        self._canonFilename = row[4]
        self._girmFilename = row[5]
        subredditsList = list()
        cursor.execute("select subreddit from subreddits where enabled = 1")
        for subreddit in cursor:
            subredditsList.append(subreddit[0])
        self._subreddits = "+".join(subredditsList)
    
    def getVersion(self):
        return self._version
        
    def getCatechismFilename(self):
        return self._catechismFilename

    def getCanonFilename(self):
        return self._canonFilename

    def getGIRMFilename(self):
        return self._girmFilename

    def getUsername(self):
        return self._username

    def getPassword(self):
        return self._password

    def getSubreddits(self):
        return self._subreddits
    
    def getDatabaseConnection(self):
        return self._connection

class Logger:
    def __init__(self, connection):
        self._connection = connection
        
    # Types are 'i' (informational), 'w' (warning), 'e' (error), 'x' (exception)
    def log(self, message, logtype="i"):
        try:
            cursor = self._connection.cursor()
            cursor.execute("insert into logs (message, type, utc_time) values(?,?,?)", (message, logtype, int(time.time())))
            self._connection.commit()
        except:
            print("Unable to log ",message,logtype,time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())," due to exception ",sys.exc_info()[0])
        
#########################################################################
# Base class for generating a catebot response. This is intended to be a parent to classes that
# implement each type of response with overrides specific to them. The classes that are expected to be
# overridden are:
#
# getResponse(self, requests)
# getContextLink(self, key, httpLocation)
# getOverflowComment(self, keys)
# linkCrossReferences(self, response)
# parsedRequests(self, requests, includeRanges = True)
#
# The initializer is called with a dictionary, a base URL for links, and a Configuration object.
#
# NOTE: The base class is implemented with the methods that are expected to be overriden. In addition to serving
# as an example of how the overrides should be written, they also implement the behavior expected when quoting
# the CCC.
#
#########################################################################
class Response:
    
    # Set up the Catechism and initialize variables
    def __init__(self, dictionary, baseURL, configuration):
        self._dictionary = dictionary
        self._baseURL = baseURL
        self._configuration = configuration

    # Just returns the current character limit for the reddit comment. Makes it easy to find/change in the future.
    # NOTE: reddit's character limit is 10,000 characters by default.
    def getCharLimit(self):
        return 8000
 
    # Simply returns the comment footer found at the bottom of every comment posted by the bot.
    def getCommentFooter(self):
        return ('\n***\n^Catebot ^' + self._configuration.getVersion() + ' ^links: [^Source ^Code](https://github.com/konohitowa/catebot)'
               + ' ^| [^Feedback](https://github.com/konohitowa/catebot/issues)' 
               + ' ^| [^Contact ^Dev](http://www.reddit.com/message/compose/?to=kono_hito_wa)'
               + ' ^| [^FAQ](https://github.com/konohitowa/catebot/blob/master/docs/CateBot%20Info.md#faq)' 
               + ' ^| [^Changelog](https://github.com/konohitowa/catebot/blob/master/docs/CHANGELOG.md)')


    def getOverflowHeader(self, singular, plural, number):
        noun = singular
        if number > 1:
            noun = plural            
        return 'The contents of the ' + noun + ' you quoted exceed the character limit ([' + str(self.getCharLimit()) + '](https://github.com/konohitowa/catebot/blob/master/docs/CateBot%20Info.md#wait-ive-counted-the-characters-and-i-didnt-hit-the-limit) characters). Instead, here are links to the ' + noun + '...\n\n'
        

    def parsedRequests(self, requests, includeRanges = True):
        validRequests = list()
        for request in requests:
            request = re.sub(r"\s+","",request)
            if ',' in request:
                sublist = request.split(',')
            else:
                sublist = [ request ]
            for subrequest in sublist:
                if '-' in subrequest:
                    startingRequest = subrequest.partition('-')[0]
                    if includeRanges:
                        endingRequest = subrequest.partition('-')[2]
                        if int(startingRequest) < int(endingRequest)+1:
                            for key in range(int(startingRequest), int(endingRequest)+1):
                                if str(key) in self._dictionary:
                                    validRequests.append(str(key))
                    else:
                        validRequests.append(startingRequest)
                elif subrequest in self._dictionary:
                        validRequests.append(subrequest)
                            
        return validRequests

    # Constructs reddit comment response for Catechism requests.
    def getResponse(self, requests):
        
        validRequests = self.parsedRequests(requests)
                        
        if len(validRequests) > 0:
            comment = ''
            for request in validRequests:
                content,location = self._dictionary[request]
                comment += ('[**CCC ' + request + '**](' + self.getContextLink(request, location) + ') ' + content) + '\n\n'
 
            comment = self.linkCrossReferences(comment)
            if len(comment) > self.getCharLimit():
                comment = self.getOverflowComment(validRequests)

            comment += self.getCommentFooter()
            return True,comment
        else:
            return False,""

    # Takes the request key and http location as parameters. The function then constructs
    # the appropriate context link. This link appears on each paragraph number.
    def getContextLink(self, request, location):
        return self._baseURL + location + '#para' + request

    # Constructs and returns an overflow comment whenever the comment exceeds the character limit set by
    # getCharLimit(). Instead of posting the contents of the request(s) in the comment, it links to webpages
    # that contain the contents of the request(s).
    def getOverflowComment(self, requests):
        numberOfRequests = 0
        comment = ''
        for request in requests:
            content,location = self._dictionary[request]
            numberOfRequests += 1
            comment += ('([' + request + '](' + self.getContextLink(request,location) + '))\n')
            if len(comment) > self.getCharLimit():
                comment += "\n\nAnd even when condensing the paragraphs to links, you still exceeded the quota..."
                break
        
        return self.getOverflowHeader('paragraph','paragraphs',numberOfRequests) + comment
    
    def linkCrossReferences(self, comment):
        xrefBlocks = reversed(list(re.finditer(r'\([\d\,\s\-]+\)$(?m)',comment)))
        for xrefBlock in xrefBlocks:
            xrefs = reversed(list(re.finditer(r'\d+',xrefBlock.group(0))))
            for xref in xrefs:
                paragraph = xref.group(0)
                content,location = self._dictionary[paragraph]
                start = xrefBlock.start()+xref.start()
                end = xrefBlock.start()+xref.end()
                comment = comment[:start]+"["+paragraph+"]("+self.getContextLink(paragraph, location)+")"+comment[end:]

        return comment

#########################################################################
#
# Constructs reddit comment response for Canon requests of form [can 12],
# [can 12s1], [can 12-14], [can 12,15-17].
#
#########################################################################
class CanonResponse(Response):
    
    def parsedRequests(self, requests, includeRanges = True):
        validRequests = list()
        for request in requests:
            request = re.sub(r"\s+","",request)
            if ',' in request:
                sublist = request.split(',')
            else:
                sublist = [ request ]
            for subrequest in sublist:
                if '-' in subrequest:
                    startingRequest = subrequest.partition('-')[0].partition('s')[0]
                    if includeRanges:
                        endingRequest = subrequest.partition('-')[2].partition('s')[0]
                        if int(startingRequest) < int(endingRequest)+1:
                            for key in range(int(startingRequest), int(endingRequest)+1):
                                if str(key) in self._dictionary:
                                    validRequests.append(str(key))
                    elif startingRequest in self._dictionary:
                        validRequests.append(startingRequest)
                else:
                    key = subrequest.partition('s')[0]
                    if key in self._dictionary:
                        validRequests.append(subrequest)
                            
        return validRequests

    def getResponse(self, requests):
        
        validRequests = self.parsedRequests(requests)

        if len(validRequests) > 0:
            comment = ''
            for request in validRequests:
                key = request.partition('s')[0]
                section = request.partition('s')[2]
                isSectioned,content,location = self._dictionary[key]
                contextLink = self.getContextLink("", location)
                if section and isSectioned:
                    try:
                        comment += ('[**Can. ' + key + '**](' + contextLink + ') ' + u"\u00A7" + section + " " + content[section]) + '\n\n'
                    except KeyError:
                        comment += '[**Can. ' + key + '**](' + contextLink + ') ' + u"\u00A7" + section + " doesn't exist\n\n"
                elif not section and isSectioned:
                    comment += '[**Can. ' + key + '**](' + contextLink + ') '
                    for sect in sorted(content.keys(),key=int):
                        comment += u"\u00A7"+sect+" "+content[sect]+"\n\n"
                else:
                    comment += '[**Can. ' + key + '**](' + contextLink + ') ' + content
                    
 
            comment = self.linkCrossReferences(comment)
            if len(comment) > self.getCharLimit():
                comment = self.getOverflowComment(validRequests)

            comment += self.getCommentFooter()
            return True,comment
        else:
            return False,""


    def getContextLink(self, dummy, location):
        return self._baseURL + location

    def getOverflowComment(self, requests):
        numberOfRequests = 0
        comment = ''
        for request in requests:
            isSectioned,content,location = self._dictionary[request]
            numberOfRequests += 1
            comment += ('([' + request + '](' + self.getContextLink("",location) + '))\n')
            if len(comment) > self.getCharLimit():
                comment += "\n\nAnd even when condensing the laws to links, you still exceeded the quota..."
                break
        
        return self.getOverflowHeader('law','laws',numberOfRequests) + comment
    
    # HERE 
    def linkCrossReferences(self,comment):
        return comment
        xrefBlocks = reversed(list(re.finditer(r'cann*\.\s+\d+$(?m)',comment)))
        for xrefBlock in xrefBlocks:
            xrefs = reversed(list(re.finditer(r'\d+',xrefBlock.group(0))))
            for xref in xrefs:
                paragraph = xref.group(0)
                content,location = self._Catechism[paragraph]
                contextLink = self.__getCanonContextLink(paragraph, location)
                start = xrefBlock.start()+xref.start()
                end = xrefBlock.start()+xref.end()
                comment = comment[:start]+"["+paragraph+"]("+contextLink+")"+comment[end:]

        return comment


#########################################################################
#
# Constructs reddit comment response for GIRM requests of form [girm n].
#
#########################################################################
class GIRMResponse(Response):

    def getResponse(self, requests):
        
        validRequests = self.parsedRequests(requests)
                        
        if len(validRequests) > 0:
            comment = ''
            for request in validRequests:
                content,location = self._dictionary[request]
                comment += ('[**GIRM ' + request + '**](' + self.getContextLink(request, location) + ') ' + content) + '\n\n'
 
            comment = self.linkCrossReferences(comment)
            if len(comment) > self.getCharLimit():
                comment = self.getOverflowComment(validRequests)

            comment += self.getCommentFooter()
            return True,comment
        else:
            return False,""

    def getContextLink(self, request, location):
        return self._baseURL + location

    def linkCrossReferences(self, comment):
        return comment
        xrefBlocks = reversed(list(re.finditer(r'\([\d\,\s\-]+\)$(?m)',comment)))
        for xrefBlock in xrefBlocks:
            xrefs = reversed(list(re.finditer(r'\d+',xrefBlock.group(0))))
            for xref in xrefs:
                paragraph = xref.group(0)
                content,location = self._dictionary[paragraph]
                start = xrefBlock.start()+xref.start()
                end = xrefBlock.start()+xref.end()
                comment = comment[:start]+"["+paragraph+"]("+self.getContextLink(paragraph, location)+")"+comment[end:]

        return comment

