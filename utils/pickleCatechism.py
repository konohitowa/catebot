#
# Creates a pickle file for the bot using the .xhtml of
# the catechism. It's assumed the files are local (it won't pull them from a URL).
#
# Usage: python pickleCatechism.py <files>
#
# NOTE: This requires HTMLParser to be installed
#

import sys
import os
import re
from HTMLParser import HTMLParser
import pickle

class CatechismParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inParagraph = False
        self.inBlockquote = False
        self.ignore = False
        self.ignoreParagraphNumber = False
        self.paragraphNumber = ""
        self.paragraphText = ""
        self.paragraphs = dict()
        self.htmlfile = ""
        # Look for elements of the form <p class="noind" style="margin-top:20px;"><i>....</i></p>
        # and skip them - they are untagged headers between paragraphs. If the score is 2, then
        # we can skip this paragraph.
        self.skipScore = 0
    
    def outputEnabled(self):
        return self.inParagraph and not self.ignore and not self.ignoreParagraphNumber
        
    def handle_starttag(self, tag, attrs):
        if(tag == "p"):
            self.skipScore = 0
            self.indent = False
            for attr in attrs:
                name,value = attr
                if(name == 'id'):
                    self.skipScore -= 1
                    para = re.match(r"para(\d+)",value)
                    if(para):
                        if(self.paragraphText != ""):
                            self.paragraphs[self.paragraphNumber] = (self.paragraphText,self.htmlfile)
                            self.paragraphText = ""
                        self.paragraphNumber = para.group(1)
                        self.paragraphs[self.paragraphNumber] = ""
                        self.inParagraph = True
                        self.ignoreParagraphNumber = True
                else:
                    if (name == "class" and value == "noind") or (name == "style" and value == "margin-top:20px;"):
                        self.skipScore += 1
                    else:
                        self.skipScore -= 1
                        if(name == "class" and value == "hang2"):
                            self.indent = True
            if self.inBlockquote:
                self.skipScore -= 1
            if self.skipScore == 2:
                self.inParagraph = False
            if self.outputEnabled():
                self.paragraphText += "\n"
                if self.inBlockquote:
                    self.paragraphText += "\n> "
                
        else:
            if tag in ["hr", "h1", "h2", "h3", "h4", "h5", "h6"]:
                self.inParagraph = False
            if(tag == "sup"):
                self.ignore = True
            if tag == "blockquote":
                self.inBlockquote = True
            if(tag == "i" and self.outputEnabled()):
                self.paragraphText += "*"
                    
    def handle_endtag(self, tag):
        if(tag == "sup"):
            self.ignore = False
        if(tag == "b"):
            if(self.ignoreParagraphNumber):
                self.ignoreParagraphNumber = False
            else:
                if(self.outputEnabled()):
                    self.paragraphText += "**"
        if(tag == "i" and self.outputEnabled()):
            self.paragraphText += "*"
        if(tag == "blockquote"):
            self.inBlockquote = False
            

    def handle_data(self, data):
        if self.outputEnabled():
            if(not self.inBlockquote):
                self.paragraphText += data.strip('\t\r')
            else:
                self.paragraphText += data.strip('\t\r\n')

    def handle_charref(self, name):
        if self.outputEnabled():
            if(name == "x201C"):
                self.paragraphText += '"'
            if(name == "x201D"):
                self.paragraphText += '"'
            if(name == "x2019"):
                self.paragraphText += '\''
            if(name in ["x2013","x2014"]):
                self.paragraphText += '-'
                if self.indent:
                    self.paragraphText += ' '
                    self.indent = False

    def cleanup(self):
        # Add the final paragraph that was processed
        if(self.paragraphText != ""):
            self.paragraphs[self.paragraphNumber] = (self.paragraphText,self.htmlfile)
        # Strip whitespace from around the text
        #self.paragraphs = {k:(v.strip(),l) for k,(v,l) in self.paragraphs.iteritems()}
        
    # Debug
    def dumpParagraphs(self):
        for key in sorted(self.paragraphs.keys(),key=int):
            print "("+key+"):"+self.paragraphs[key]
            
    def pickle(self,file):
        pickle.dump(self.paragraphs,file)
        
    def setHTMLFile(self, htmlfile):
        self.htmlfile = htmlfile
        
parser = CatechismParser()

for arg in sys.argv[1:]:
    htmlFile = os.path.basename(arg)
    parser.setHTMLFile(htmlFile)
    parser.feed(open(arg,'r').read())

parser.cleanup()
pickled = open('catechism.pickle','wb')
parser.pickle(pickled)
pickled.close()
#parser.dumpParagraphs()
