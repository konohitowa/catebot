#
# Creates a pickle file for the bot using the .html of
# the canon law. It's assumed the files are local (it won't pull them from a URL).
#
# Usage: python pickleCanon.py <files>
#
# NOTE: This requires HTMLParser to be installed
#
# <p ...>Can\.\s+\d+\s+&sect;\d+\.\s+...</p>
# <p ...>&sect;\d+\.\s+...</p>
# <p ...>Can\.\s*
#    \s*\d+...</p>
# <p ...>Can...</p>
# <p ...>...</p>
# <p ...>...</p>
# <p ...>Can...</p>...
#
# references: can. cann.

import sys
import os
import re
from HTMLParser import HTMLParser
import pickle

class CanonParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inCanonLaw = False
        self.startOfParagraph = False
        self.ignore = False
        self.currentLawNumber = False
        self.lawText = ""
        self.laws = dict()
        self.htmlfile = ""
    
# law[lawNumber] = (True,dict())
# law[lawnumber] = (False,text())
    def outputEnabled(self):
        return self.inCanonLaw and not self.ignore
        
    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.startOfParagraph = True
            self.startOfSection = False
            for attr in attrs:
                name,value = attr
                if name == 'align' and value == 'center':
                    self.inCanonLaw = False
                    self.addLaw()
                
        if tag == "i" and self.outputEnabled():
            self.lawText += "*"
            
        if tag == "center":
            self.inCanonLaw = False
                    
    def handle_endtag(self, tag):
        if tag == "i" and self.outputEnabled():
            self.lawText += "*"
        if tag == "p" and self.outputEnabled():
            self.lawText += "\n\n"
            

    def handle_data(self, data):
        if self.startOfParagraph:
            if re.match(r"^Can\.",data):
                self.inCanonLaw = True
                self.addLaw()
            if self.startOfSection:
                self.addLaw()
                self.lawText = "\xc2"
            self.startOfParagraph = False
            self.startOfSection = False
        if self.outputEnabled():
            self.lawText += re.sub(r"[\r\t\n]+"," ",data.strip('\t\r\n'))

    def handle_entityref(self, name):
        if self.outputEnabled():
            if(name == "sect"):
                self.lawText += "\xc2"
                self.startOfSection = True
            if(name == "nbsp"):
                self.lawText += " "
        
    def handle_charref(self, name):
        if self.outputEnabled():
            if(name == "x201C"):
                self.lawText += '"'
            if(name == "x201D"):
                self.lawText += '"'
            if(name == "x2019"):
                self.lawText += '\''
            if(name in ["x2013","x2014"]):
                self.lawText += '-'

    def addLaw(self):
        if self.lawText:
            lawMatch = re.match(r"^Can\.\s+(\d+)",self.lawText)
            sectionMatch = re.match(r"^\xc2\s*(\d+)",self.lawText)
            lawSectionMatch = re.match(r"^Can\.\s+(\d+)\s*\xc2\s*(\d+)",self.lawText)
        
            if lawMatch:
                self.currentLawNumber = lawMatch.group(1)
            sectionNumber = False
            if sectionMatch:
                sectionNumber = sectionMatch.group(1)
            if lawSectionMatch:
                sectionNumber = lawSectionMatch.group(2)
            
            self.lawText = re.sub(r"^Can\.\s+\d+\.*\s*","",self.lawText)
            self.lawText = re.sub(r"^Can\.\s+\d+\s+\xc2\s*\d+\.*\s*","",self.lawText)
            self.lawText = re.sub(r"^\xc2\s*\d+\.*\s*","",self.lawText)
            self.lawText = self.lawText.rstrip('\xc2')
            self.lawText = re.sub(r"\xc2(?m)",u"\u00A7",self.lawText)
            self.lawText = re.sub(r"/ (?m)",". ",self.lawText)
            
            if sectionNumber:
                try:
                    dummyflag,sectionList,dummyfilename = self.laws[self.currentLawNumber]
                except KeyError:
                    sectionList = dict()
                sectionList[sectionNumber] = self.lawText
                self.laws[self.currentLawNumber] = (True,sectionList,self.htmlfile)
            else:
                self.laws[self.currentLawNumber] = (False,self.lawText,self.htmlfile)
        
            self.lawText = ""
        
    # Debug
    def dumpLaws(self):
        for key in sorted(self.laws.keys(),key=int):
            isDict,law,htmlfile = self.laws[key]
            if not isDict:
                print("Can. "+key+" "+law)
            else:
                for sect in sorted(law.keys(),key=int):
                    print("Can. "+key+" \xc2"+sect+" "+law[sect])
            
    def pickle(self,file):
        pickle.dump(self.laws,file)
        
    def setHTMLFile(self, htmlfile):
        self.htmlfile = htmlfile
        
parser = CanonParser()

for arg in sys.argv[1:]:
    htmlFile = os.path.basename(arg)
    parser.setHTMLFile(htmlFile)
    parser.feed(open(arg,'r').read())
    parser.addLaw()

pickled = open('canon.pickle','wb')
parser.pickle(pickled)
pickled.close()
#parser.dumpLaws()
