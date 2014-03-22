import re
import sqlite3
import time

class Configuration:
    
    def __init__(self, databaseFilename):
        self._connection = sqlite3.connect(databaseFilename)
        self._connection.row_factory = sqlite3.Row
        cursor = self._connection.cursor()
        cursor.execute("select version,username,password,catechismFilename from configuration")
        row = cursor.fetchone()
        self._version = row[0]
        self._username = row[1]
        self._password = row[2]
        self._catechismFilename = row[3]
        subredditsList = list()
        cursor.execute("select subreddit from subreddits where enabled = 1")
        for subreddit in cursor:
            subredditsList.append(subreddit[0])
        self._subreddits = "+".join(subredditsList)
    
    def getVersion(self):
        return self._version
        
    def getCatechismFilename(self):
        return self._catechismFilename

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
        
# Class that holds the properties of a Catechism paragraph. This includes the paragraph number and xhtml
# file from which it was extracted as well as the text of the paragraph.
# Also within this class are multiple methods used by Catebot.
class Response:
    
    _Catechism = dict()

    # Set up the Catechism and initialize variables
    def __init__(self, catechism, configuration):
        self._Catechism = catechism
        self._configuration = configuration
        self.cccurl = 'http://www.usccb.org/beliefs-and-teachings/what-we-believe/catechism/catechism-of-the-catholic-church/epub/OEBPS/'

    # Constructs reddit comment response.
    def getResponse(self, paragraphRequests):
        
        validParagraphList = self.__parsedParagraphs(paragraphRequests)
                        
        if len(validParagraphList) > 0:
            comment = ''
            for paragraph in validParagraphList:
                content,location = self._Catechism[paragraph]
                contextLink = self.__getContextLink(paragraph, location)
                comment += ('[**' + paragraph + '**](' + contextLink + ') ' + content) + '\n\n'
 
            comment = self.__linkCrossReferences(comment)
            if len(comment) > self.__getCharLimit():
                comment = self.__getOverflowComment(validParagraphList)

            comment += self.__getCommentFooter()
            return True,comment
        else:
            return False,""

    # Just returns the current character limit for the reddit comment. Makes it easy to find/change in the future.
    # NOTE: reddit's character limit is 10,000 characters by default.
    def __getCharLimit(self):
        return 8000
 
    # Simply returns the comment footer found at the bottom of every comment posted by the bot.
    def __getCommentFooter(self):
        return ('\n***\n^Catebot ^' + self._configuration.getVersion() + ' ^links: [^Source ^Code](https://github.com/konohitowa/catebot)'
               + ' ^| [^Feedback](https://github.com/konohitowa/catebot/issues)' 
               + ' ^| [^Contact ^Dev](http://www.reddit.com/message/compose/?to=kono_hito_wa)'
               + ' ^| [^FAQ](https://github.com/konohitowa/catebot/blob/master/docs/CateBot%20Info.md#faq)' 
               + ' ^| [^Changelog](https://github.com/konohitowa/catebot/blob/master/docs/CHANGELOG.md)')

    # Takes the paragraph number and xhtml location as parameters. The function then constructs
    # the appropriate context link. This link appears on each paragrpah number.
    def __getContextLink(self, paragraph, location):
        link = self.cccurl + location + '#para' + paragraph
        return link

    # Constructs and returns an overflow comment whenever the comment exceeds the character limit set by
    # __getCharLimit(). Instead of posting the contents of the paragraphs(s) in the comment, it links to webpages
    # that contain the contents of the paragraphs(s).
    def __getOverflowComment(self, paragraphList):
        numberOfParagraphs = 0
        comment = ''
        for paragraph in paragraphList:
            content,location = self._Catechism[paragraph]
            numberOfParagraphs += 1
            overflowLink = self.cccurl + location + '#para' + paragraph
            comment += ('([' + paragraph + '](' + overflowLink + '))\n')
            if len(comment) > self.__getCharLimit():
                comment += "\n\nAnd even when condensing the paragraphs to links, you still exceeded the quota..."
                break
        
        # Handle plural of 'paragraph'
        properNumber = 'paragraph'
        if numberOfParagraphs > 1:
            properNumber += 's'
            
        header = 'The contents of the ' + properNumber + ' you quoted exceed the character limit ([' + str(self.__getCharLimit()) + '](https://github.com/konohitowa/catebot/blob/master/docs/CateBot%20Info.md#wait-ive-counted-the-characters-and-i-didnt-hit-the-limit) characters). Instead, here are links to the ' + properNumber + '...\n\n'
        comment = header + comment
        
        return comment
    
    def __linkCrossReferences(self,comment):
        xrefBlocks = reversed(list(re.finditer(r'\([\d\,\s\-]+\)$(?m)',comment)))
        for xrefBlock in xrefBlocks:
            xrefs = reversed(list(re.finditer(r'\d+',xrefBlock.group(0))))
            for xref in xrefs:
                paragraph = xref.group(0)
                content,location = self._Catechism[paragraph]
                contextLink = self.__getContextLink(paragraph, location)
                start = xrefBlock.start()+xref.start()
                end = xrefBlock.start()+xref.end()
                comment = comment[:start]+"["+paragraph+"]("+contextLink+")"+comment[end:]

        return comment
    
    def __parsedParagraphs(self, paragraphRequests, includeRanges = True):
        validParagraphList = list()
        for paragraph in paragraphRequests:
            if ',' in paragraph:
                sublist = paragraph.split(',')
            else:
                sublist = [ paragraph ]
            for subpara in sublist:
                if '-' in subpara:
                    startingPar = subpara.partition('-')[0]
                    if includeRanges:
                        endingPar = subpara.partition('-')[2]
                        if int(startingPar) < int(endingPar)+1:
                            for par in range(int(startingPar), int(endingPar)+1):
                                if str(par) in self._Catechism:
                                    validParagraphList.append(str(par))
                    else:
                        validParagraphList.append(startingPar)
                else:
                    if subpara in self._Catechism:
                        validParagraphList.append(subpara)
                            
        return validParagraphList
