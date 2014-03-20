# Simple program to pull paragraphs from the pickled CCC
# for testing purposes.
#
# Usage: python getParagraph.py catechism.pickle <paragraph number> [<paragraph number> ...]
#

import sys
import os
import re
import pickle

catechism = pickle.load(open(sys.argv[1], 'rb'))

for arg in sys.argv[2:]:
    text, location = catechism[arg]
    print("(",arg,")->",location,text)
