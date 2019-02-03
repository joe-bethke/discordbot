import sys
import os
from random import randint
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import data_tracking

DEFAULT_SERVER = 211220170230857728


class IDTest(object):
    def __init__(self, id):
        self.id = id


x = data_tracking.MemberDocument(IDTest(DEFAULT_SERVER), IDTest(randint(1, 10000)))
print(x)
