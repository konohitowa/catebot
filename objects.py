import re
import sqlite3
import time

class Configuration:
    
    def __init__(self, databaseFilename, sandbox=False):
        self._connection = sqlite3.connect(databaseFilename)
        self._connection.row_factory = sqlite3.Row
        cursor = self._connection.cursor()
        cursor.execute("select * from configuration")
        row = cursor.fetchone()
        self._version = row['version']
        self._username = row['username']
        self._password = row['password']
        self._clientId = row['clientId']
        self._clientSecret = row['clientSecret']
        self._catechismFilename = row['catechismFilename']
        self._baltimoreFilename = row['baltimoreFilename']
        self._canonFilename = row['canonFilename']
        self._girmFilename = row['girmFilename']
        subredditsList = list()
        if sandbox:
            condition = "sandbox = 1"
        else:
            condition = "enabled = 1"
        cursor.execute("select subreddit from subreddits where " + condition)
        for subreddit in cursor:
            subredditsList.append(subreddit[0])
        self._subreddits = "+".join(subredditsList)
    
    def getVersion(self):
        return self._version
        
    def getCatechismFilename(self):
        return self._catechismFilename

    def getBaltimoreFilename(self):
        return self._baltimoreFilename

    def getCanonFilename(self):
        return self._canonFilename

    def getGIRMFilename(self):
        return self._girmFilename

    def getUsername(self):
        return self._username

    def getPassword(self):
        return self._password

    def getClientId(self):
        return self._clientId

    def getClientSecret(self):
        return self._clientSecret

    def getSubreddits(self):
        return self._subreddits
    
    def getDatabaseConnection(self):
        return self._connection

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
        return 9500
 
    # Simply returns the comment footer found at the bottom of every comment posted by the bot.
    def getCommentFooter(self):
        return ('\n***\nCatebot ' + self._configuration.getVersion() + ' links: [Source Code](https://github.com/konohitowa/catebot)'
               + ' | [Feedback](https://github.com/konohitowa/catebot/issues)' 
               + ' | [Contact Dev](http://www.reddit.com/message/compose/?to=kono_hito_wa)'
               + ' | [FAQ](https://github.com/konohitowa/catebot/blob/master/docs/CateBot%20Info.md#faq)' 
               + ' | [Changelog](https://github.com/konohitowa/catebot/blob/master/docs/CHANGELOG.md)')


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
        return 'http://www.scborromeo.org/ccc/para/' + request + '.htm'

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
# Constructs reddit comment response for Balitmore Catechism requests of
# the form [bccd 1], [bccd 1-5], [bccd 1-5,9-10], and the same forms with
# a BCCD book #, such as [bccd #1 1-5, 10-12]. The default book is #2.
#
#########################################################################
class BaltimoreResponse(Response):
    
    def parsedRequests(self, requests, includeRanges = True):
        validRequests = list()
        for taggedRequest in requests:
            bookNumber = '2'
            bookRequest, request = taggedRequest
            bookRequest = re.sub(r"\s+","",bookRequest)
            request = re.sub(r"\s+","",request)
            bookMatch = re.match(r'#(\d+)', bookRequest)
            if bookMatch:
                bookNumber = bookMatch.group(1)
                if int(bookNumber) < 1 or int(bookNumber) > 4:
                    bookNumber = '2'
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
                                if str(key) in self._dictionary[bookNumber]:
                                    validRequests.append({'Book': bookNumber, 'Request': str(key)})
                    elif startingRequest in self._dictionary[bookNumber]:
                        validRequests.append({'Book': bookNumber, 'Request': startingRequest})
                elif subrequest in self._dictionary[bookNumber]:
                        validRequests.append({'Book': bookNumber, 'Request': subrequest})
                            
        return validRequests

    def getResponse(self, requests):
        
        validRequests = self.parsedRequests(requests)

        if len(validRequests) > 0:
            comment = ''
            for request in validRequests:
                bookNumber = request['Book']
                requestNumber = request['Request']
                qa = self._dictionary[bookNumber][requestNumber]
                comment += ('[**BCCD #' + bookNumber + " Q." + requestNumber + '**](' + self.getContextLink(bookNumber, requestNumber, qa['Q']) + ') ' + qa['Q'] + '\n\nA. ' + qa['A']) + '\n\n'
 
            comment = self.linkCrossReferences(comment)
            if len(comment) > self.getCharLimit():
                comment = self.getOverflowComment(validRequests)

            comment += self.getCommentFooter()
            return True,comment
        else:
            return False,""

    # This needs to be updated when an actual linkable source is available
    #q.2_who_is_god.3F #self._baseURL
    def getContextLink(self, bookNumber, questionNumber, questionText):
        modifiedQuestionText = re.sub(r'\s','_',questionText).lower()
        modifiedQuestionText = re.sub(r',','.2C',modifiedQuestionText)
        modifiedQuestionText = re.sub(r'\?','.3F',modifiedQuestionText)
        partitionText = ""
        if int(bookNumber) == 4:
            partitionText = "_"
            if int(questionNumber) < 211:
                partitionText += "1"
            else:
                partitionText += "2"
        return 'https://www.reddit.com/r/Catebot/wiki/bccd_' + bookNumber + partitionText + '#wiki_q.' + questionNumber + '_' + modifiedQuestionText

    def getOverflowComment(self, requests):
        numberOfRequests = 0
        comment = ''
        for request in requests:
            numberOfRequests += 1
            bookNumber = request['Book']
            requestNumber = request['Request']
            qa = self._dictionary[bookNumber][requestNumber]
            comment += ('([' + requestNumber + '](' + self.getContextLink(bookNumber, requestNumber, qa['Q']) + '))\n')
            if len(comment) > self.getCharLimit():
                comment += "\n\nAnd even when condensing the requested questions to links, you still exceeded the quota..."
                break
        
        return self.getOverflowHeader('question','questions',numberOfRequests) + comment
    
    # This needs to be filled out for the {} references in #3
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

