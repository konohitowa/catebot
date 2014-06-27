# Simple program to pull paragraphs from the pickled GIRM
# for testing purposes.
#
# Usage: python getGIRM.py girm.pickle <paragraph number> [<paragraph number> ...]
#

import sys
import os
import re
import pickle

girm = pickle.load(open(sys.argv[1], 'rb'))

if sys.argv[2] == '-a':
    for key in sorted(girm.keys(),key=int):
        text, location = girm[key]
        print("("+key+")->"+text)
else:
    for arg in sys.argv[2:]:
        text, location = girm[arg]
        print("("+arg+")->"+text)
