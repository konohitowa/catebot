#!/usr/bin/python
#
# Creates a pickle file for the bot using the .xhtml of
# the catechism. It's assumed the files are local (it won't pull them from a URL).
#
# Usage: python pickleBaltimore.py <files>
#
#

import sys
import os
import re
import pickle

class CatechismParser:
    def __init__(self):
        self.inQuestion = False
        self.inAnswer = False
        self.ignore = False
        self.questionNumber = None
        self.questionText = None 
	self.answerText = None 
	self.catechisms = dict()
        self.questions = dict()
    
    def outputEnabled(self):
        return self.inParagraph and not self.ignore and not self.ignoreParagraphNumber

    def parse(self, lines):
        self.questions = dict()
        for line in lines:
            questionMatch = re.match(r'\*?(\d+)\.?\sQ\.\s(.*)|\*?Q\.\s(\d+)\.?\s(.*)', line)
            answerMatch = re.match(r'A\.\s(.*)', line)
            stopAnswer = re.match(r'STOP_PARSING|LESSON', line)
            
            if stopAnswer and self.inAnswer:
                self.questions[self.questionNumber] = { 'Q': self.questionText, 'A': self.answerText }
                self.inAnswer = False
            elif questionMatch:
                if self.inAnswer:
                    self.questions[self.questionNumber] = { 'Q': self.questionText, 'A': self.answerText }
                    self.inAnswer = False
                groupIndex = 1
                if questionMatch.group(3):
                    groupIndex = 3
                self.questionNumber = questionMatch.group(groupIndex)
                self.questionText = questionMatch.group(groupIndex+1).rstrip()
                self.inQuestion = True
            elif answerMatch:
                self.answerText = answerMatch.group(1).rstrip()
                self.inAnswer = True
                self.inQuestion = False
            elif self.inQuestion:
                self.questionText += " " + line.lstrip().rstrip()
            elif self.inAnswer:
                if len(line.lstrip().rstrip()) > 0:
                    self.answerText += " " + line.lstrip().rstrip()
                else:
                    self.answerText += "\n\n"
	        
    def cleanup(self, bookNumber):
        # Add the final paragraph that was processed
        if self.inAnswer:
            self.inAnswer = False
            self.questions[self.questionNumber] = { 'Q': self.questionText, 'A': self.answerText }

        self.catechisms[bookNumber] = self.questions
        
    # Debug
    def dumpQuestions(self):
        for book in sorted(self.catechisms.keys(),key=int):
            for key in sorted(self.catechisms[book].keys(),key=int):
                print book +"("+key+"):\n\tQ. "+self.catechisms[book][key]['Q']+"\n\tA. " + self.catechisms[book][key]['A']
            
    def pickle(self,file):
        pickle.dump(self.catechisms,file)
        
parser = CatechismParser()

for arg in sys.argv[1:]:
    textFile = os.path.basename(arg)
    bccdNumber = re.match(r'bccd_(\d)', arg)
    if bccdNumber:
        parser.parse(open(arg,'r').readlines())
        parser.cleanup(bccdNumber.group(1))

#parser.dumpQuestions()
pickled = open('baltimore.pickle','wb')
parser.pickle(pickled)
pickled.close()
