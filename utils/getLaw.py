# Simple program to pull laws from the pickled Canon Law
# for testing purposes.
#
# Usage: python getParagraph.py catechism.pickle <law number>[s<section number>] [...]
#

import sys
import os
import re
import pickle

import pdb

canon = pickle.load(open(sys.argv[1], 'rb'))

for arg in sys.argv[2:]:
#    pdb.set_trace()
    sectionRequest = re.match(r"(\d+)s(\d+)",arg)
    if sectionRequest:
        lawNumber = sectionRequest.group(1)
        sectionNumber = sectionRequest.group(2)
    else:
        lawNumber = arg
        sectionNumber = False
    
#    try:
    isSectioned,law,htmlfile = canon[lawNumber]
    print("HTML file => ",htmlfile)
    lawText = "Can. "+lawNumber+" "
    if isSectioned and not sectionNumber:
        for sect in sorted(law.keys(),key=int):
            lawText += u"\u00A7"+sect+". "+law[sect]+"\n"
    elif isSectioned and sectionNumber:
        try:
            lawText += u"\u00A7"+sectionNumber+". "+law[sectionNumber]
        except KeyError:
            print "There is no section "+sectionNumber+" in Can. "+lawNumber
            lawText = ""
    elif not isSectioned and not sectionNumber:
        lawText += law
    else:
        print "There is no section "+sectionNumber+" in Can. "+lawNumber
        lawText = ""

    if lawText:
        print lawText.encode('utf-16')
            
#    except:
#        pdb.set_trace()
#        print "Invalid request "+arg