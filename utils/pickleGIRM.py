#
# Creates a pickle file for the bot using the .xhtml of
# the catechism. It's assumed the files are local (it won't pull them from a URL).
#
# Usage: python pickleCatechism.py <files>
#
# NOTE: This requires HTMLParser to be installed
#

import os
import pickle
import re
import sys

from HTMLParser import HTMLParser

class GIRMParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inParagraph = False
        self.ignore = False
        self.paragraphText = u""
        self.paragraphs = dict()
        self.htmlfile = ""
    
    def outputEnabled(self):
        return self.inParagraph and not self.ignore
        
    def handle_starttag(self, tag, attrs):
        if(tag == "p"):
            for attr in attrs:
                name,value = attr
                if(name == 'class' and value == 'parafirst'):
                    self.inParagraph = True
                    break
        elif(tag == "a"):
                 for attr in attrs:
                     name,value = attr
                     if(name == 'class' and value == 'footnote-link'):
                         self.ignore = True
                         break
        elif(tag == "b" and self.outputEnabled()):
            self.paragraphText += u"**"
        elif(tag == "i" and self.outputEnabled()):
            self.paragraphText += u"*"
                    
    def handle_endtag(self, tag):
        if(tag == "p"):
            self.inParagraph = False
            self.addText()
        elif(tag == "b" and self.outputEnabled()):
            self.paragraphText += u"**"
        elif(tag == "i" and self.outputEnabled()):
            self.paragraphText += u"*"
        elif(tag == "a"):
            self.ignore = False
            

    def handle_data(self, data):
        if self.outputEnabled():
            stripped = data.decode('utf-8').strip('\t\r')
            self.paragraphText += stripped

    def handle_charref(self, name):
        if self.outputEnabled():
            if(name == "x201C"):
                self.paragraphText += u'"'
            elif(name == "x201D"):
                self.paragraphText += u'"'
            elif(name == "x2019"):
                self.paragraphText += u'\''
            elif(name in ["x2013","x2014"]):
                self.paragraphText += u'-'

    def addText(self):
        if self.paragraphText != u'':
            paragraphNumberMatch = re.match(r'^(\d+)',self.paragraphText)
            if paragraphNumberMatch:
                paragraphNumber = paragraphNumberMatch.group(0)
                self.paragraphText = re.sub(r'^\d+\.\s+',u"",self.paragraphText)
                self.paragraphs[paragraphNumber] = (self.paragraphText, self.htmlfile)
                self.paragraphText = u""
        
    # Debug
    def dumpParagraphs(self):
        for key in sorted(self.paragraphs.keys(),key=int):
            text,location = self.paragraphs[key]
            print "("+key+"):"+text+"@"+location
            
    def pickle(self,file):
        pickle.dump(self.paragraphs,file,-1)
        
    def setHTMLFile(self, htmlfile):
        self.htmlfile = htmlfile
        
parser = GIRMParser()

for arg in sys.argv[1:]:
    htmlFile = os.path.basename(arg)
    parser.setHTMLFile(htmlFile)
    parser.feed(open(arg,'r').read())

pickled = open('girm.pickle','wb')
parser.pickle(pickled)
pickled.close()
#parser.dumpParagraphs()
