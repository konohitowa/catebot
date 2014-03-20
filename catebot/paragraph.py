from re import findall
from re import sub
from re import subn
#import booknames

# Class that holds the properties of a Catechism paragraph. This includes the paragraph number and xhtml
# file from which it was extracted as well as the text of the paragraph.
# Also within this class are multiple methods used by Catebot.
class Paragraph:
    
    _paragraphData = list()
    _Catechism = dict()
    _invalidComment = False

    # Initializes Paragraph object with data from the command(s)
    def __init__(self, paragraphList, catechism):
        self._Catechism = catechism
        self.cccurl = 'http://www.usccb.org/beliefs-and-teachings/what-we-believe/catechism/catechism-of-the-catholic-church/epub/OEBPS/'
        
        for paragraph in paragraphList:
            try:
                if ',' in paragraph:
                    sublist = paragraph.split(',')
                else:
                    sublist = [ paragraph ]
                for subpara in sublist:
                    if '-' in subpara:
                        startingPar = subpara.partition('-')[0]
                        endingPar = subpara.partition('-')[2]
                        if int(startingPar) < int(endingPar)+1:
                            for par in range(int(startingPar), int(endingPar)+1):
                                self._paragraphData.append((str(par),self._Catechism[str(par)]))
                    else:
                        self._paragraphData.append((subpara,self._Catechism[subpara]))
                        
            except KeyError:
                print("Invalid paragraph:",paragraph,paragraphList)
        
        if len(self._paragraphData) == 0:
            self._invalidComment = True

        return
        
    def linkCrossReferences(self,comment):

        crossReferences = findall(r'\(([\d\,\s\-]+)\)$(?m)',comment)
        if len(crossReferences) != 0:
            for eachRef in crossReferences:
                strippedRef = sub(r'\s+','',str(eachRef))
                paragraphList = [ strippedRef ]
                for paragraph in paragraphList:
                    if ',' in paragraph:
                        sublist = paragraph.split(',')
                    else:
                        sublist = [ paragraph ]
                    for subpara in sublist:
                        if '-' in subpara:
                            par = subpara.partition('-')[0]
                        else:
                            par = subpara
                        content,location = self._Catechism[par]
                        contextLink = self.__getContextLink(par, location)
                        # Just do all four cases... it's easier than figuring it out or tracking it
                        comment,subs = subn(r'\(%s\)(?m)'%par,"(["+par+"]("+contextLink+"))", comment)
                        if subs == 0:
                            comment,subs = subn(r'%s, (?m)'%par,"["+par+"]("+contextLink+"), ", comment)
                        if subs == 0:
                            comment,subs = subn(r'%s-(?m)'%par,"["+par+"]("+contextLink+")-", comment)
                        if subs == 0:
                            comment,subs = subn(r'%s\)(?m)'%par,"["+par+"]("+contextLink+"))", comment)

        return comment
            
    # Constructs reddit comment.
    def getComment(self):
        if not self._invalidComment:
            comment = ''
            for curParData in self._paragraphData:
                paragraph = curParData[0]
                content,location = curParData[1]
                contextLink = self.__getContextLink(paragraph, location)
                comment += ('[**' + paragraph + '**](' + contextLink + ') ' + content) + '\n\n'
 
            comment = self.linkCrossReferences(comment)
            if len(comment) > self.__getCharLimit():
                comment = self.__getOverflowComment()

            comment += self.__getCommentFooter()
            return comment
        else:
            return False

    # Clears contents of _paragraphData.
    def clearParagraphs(self):
        self._paragraphData.clear()
        return
    
    # Simply returns the comment footer found at the bottom of every comment posted by the bot.
    def __getCommentFooter(self):
        return ('\n***\n^Catebot ^links: [^Source ^Code](https://github.com/konohitowa/catebot)'
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
    def __getOverflowComment(self):
        numberOfParagraphs = 0
        comment = ''
        for curParData in self._paragraphData:
            paragraph = curParData[0]
            content,location = curParData[1]
            numberOfParagraphs += 1
            
            overflowLink = self.cccurl + location + '#para' + paragraph

            comment += ('([' + paragraph + '](' + overflowLink + '))\n')
        
        properNumber = 'paragraph'
        if numberOfParagraphs > 1:
            properNumber += 's'
            
        header = 'The contents of the ' + properNumber + ' you quoted exceed the character limit (4000 characters). Instead, here are links to the ' + properNumber + '...\n\n'
        comment = header + comment
        
        return comment
    
    # Just returns the current character limit for the reddit comment. Makes it easy to find/change in the future.
    # NOTE: reddit's character limit is 10,000 characters by default.
    def __getCharLimit(self):
        return 4000



