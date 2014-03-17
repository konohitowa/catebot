from collections import OrderedDict
from re import findall
#import booknames

# Class that holds the properties of a Catechism paragraph. This includes the paragraph, chapter,
# verse (or range of verses), and translation. Also within this class are multiple
# methods used by Catebot.
class Paragraph:
    
    _paragraphData = list()
    _Catechism = dict()
    _invalidComment = False

    # Initializes Paragraph object with data from the command(s)
    def __init__(self, paragraphList, catechism):
        self._Catechism = catechism
        
        for paragraph in paragraphList:
            try:
                if '-' in paragraph:
                    startingPar = paragraph.partition('-')[0]
                    endingPar = paragraph.partition('-')[2]
                    if int(startingPar) < int(endingPar)+1:
                        for par in range(int(startingPar), int(endingPar)+1):
                            self._paragraphData.append((str(par),self._Catechism[str(par)]))
                else:
                    if ',' in paragraph:
                        for par in paragraph.split(','):
                            self._paragraphData.append((par,self._Catechism[par]))
                    else:
                        
                        self._paragraphData.append((paragraph,self._Catechism[paragraph]))
                        
            except KeyError:
                print("Invalid paragraph:",paragraph,paragraphList)
        
        if len(self._paragraphData) == 0:
            self._invalidComment = True

        return

    # Constructs reddit comment.
    def getComment(self):
        if not self._invalidComment:
            comment = ''
            for curParData in self._paragraphData:
                # These assignments technically aren't necessary, it just makes the code below a lot easier to
                # understand.
                paragraph = curParData[0]
                content = curParData[1]
                #contextLink = self.__getContextLink(book, chap, translation)
                contextLink = ''
#                if ver != '0':
                comment += ('(' + paragraph + ') ' + content) + '\n\n'
                
                #else:
                #    comment += ('[**' + book + ' ' + chap + ' (*' + translation + '*)**](' + 
                #                contextLink + ')\n>' + content) + '\n\n'

            #if 0 < len(comment) <= self.__getCharLimit():
            comment += self.__getCommentFooter()
            return comment
            #else:
            #    comment = self.__getOverflowComment()
            #    comment += self.__getCommentFooter()
            #    return comment
        else:
            return False

    # Clears contents of _verseData.
    def clearParagraphs(self):
        self._paragraphData.clear()
        return
    
    # Simply returns the comment footer found at the bottom of every comment posted by the bot.
    def __getCommentFooter(self):
        return ('\n***\n[[Source Code](https://github.com/konohitowa/catebot)]'
               + ' [[Feedback](https://github.com/konohitowa/catebot/issues)]' 
               + ' [[Contact Dev](http://www.reddit.com/message/compose/?to=kono_hito_wa)]'
               + ' [[FAQ](https://github.com/konohitowa/catebot/blob/master/docs/CateBot%20Info.md#faq)]' 
               + ' [[Changelog](https://github.com/konohitowa/catebot/blob/master/docs/CHANGELOG.md)]')

    # Takes the verse's book name, chapter, and translation as parameters. The function then constructs
    # the appropriate context link. This link appears on each verse title.
    def __getContextLink(self, bookName, chap, translation):
        if translation == 'Brenton\'s Septuagint':
            link = ('http://studybible.info/Brenton/' + bookName + '%20' + chap).replace(' ', '%20')
        elif translation == 'KJV Deuterocanon':
            link = ('http://kingjamesbibleonline.org/' + bookName + '-Chapter-' + chap + '/').replace(' ', '-')
        elif translation == 'JPS Tanakh':
            link = ('http://www.taggedtanakh.org/Chapter/Index/english-' + booknames.getTanakhName(bookName) + '-' + chap)
        elif translation == 'Nova Vulgata':
            novaNum = booknames.getBookNumber(bookName.lower())
            if novaNum <= 39: # The Vatican website URL is different for Old Testament (Vetus Testamentum) and New Testament (Novum Testamentum)
                if novaNum == 19: # Links to Psalms are formatted differently on http://vatican.va/
                    link = ('http://www.vatican.va/archive/bible/nova_vulgata/documents/nova-vulgata_vt_psalmorum_lt.html#PSALMUS%20' + chap)
                else:
                    link = ('http://www.vatican.va/archive/bible/nova_vulgata/documents/nova-vulgata_vt_' + booknames.getNovaName(bookName) + '_lt.html#' + chap)
            else:
                link = ('http://www.vatican.va/archive/bible/nova_vulgata/documents/nova-vulgata_nt_' + booknames.getNovaName(bookName) + '_lt.html#' + chap)
        else:
            link = ('http://www.biblegateway.com/passage/?search=' + bookName + '%20' + chap + '&version=' + translation).replace(' ', '%20')

        return link

    # Constructs and returns an overflow comment whenever the comment exceeds the character limit set by
    # __getCharLimit(). Instead of posting the contents of the verse(s) in the comment, it links to webpages
    # that contain the contents of the verse(s).
    def __getOverflowComment(self):
        comment = 'The contents of the verse(s) you quoted exceed the character limit (4000 characters). Instead, here are links to the verse(s)!\n\n'
        for curVerData in self._verseData:
            book = curVerData[0]
            chap = curVerData[1]
            ver = curVerData[2]
            translation = curVerData[3]

            if translation == 'Brenton\'s Septuagint':
                if ver != '0':
                    overflowLink = ('http://www.studybible.info/Brenton/' + book + '%20' + chap + ':' + ver).replace(' ', '%20')
                else:
                    overflowLink = ('http://www.studybible.info/Brenton/' + book + '%20' + chap).replace(' ', '%20')
            elif translation == 'KJV Deuterocanon':
                 if ver != '0':
                    overflowLink = ('http://www.kingjamesbibleonline.org/' + book + '-' + chap + '-' + ver + '/').replace(' ', '-')
                 else:
                    overflowLink = ('http://www.kingjamesbibleonline.org/' + book + '-Chapter-' + chap + '/').replace(' ', '-')
            elif translation == 'JPS Tanakh':
                 overflowLink = ('http://www.taggedtanakh.org/Chapter/Index/english-' + booknames.getTanakhName(book) + '-' + chap)
            elif translation == 'Nova Vulgata':
                overflowLink = self.__getContextLink(book, chap, translation)
            else:
                if ver != '0':
                    overflowLink = ('http://www.biblegateway.com/passage/?search=' + book + '%20' + chap + ':' + 
                                    ver + '&version=' + translation).replace(' ', '%20')
                else:
                    overflowLink = ('http://www.biblegateway.com/passage/?search=' + book + '%20' + chap + 
                                 '&version=' + translation).replace(' ', '%20')

            if ver != '0':
                comment += ('- [' + book + ' ' + chap + ':' + ver + ' (' + translation + ')](' + overflowLink + ')\n')
            else:
                comment += ('- [' + book + ' ' + chap + ' (' + translation + ')](' + overflowLink + ')\n')
        
        return comment
    
    # Just returns the current character limit for the reddit comment. Makes it easy to find/change in the future.
    # NOTE: reddit's character limit is 10,000 characters by default.
    def __getCharLimit(self):
        return 4000



