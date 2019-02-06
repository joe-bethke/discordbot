from dotenv import load_dotenv
import os
from pymongo import MongoClient
from random import randint
import sys
import time
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

load_dotenv("auth.env")
CLIENT = MongoClient(os.getenv("DISCORD_MONGO"))
SERVER_TRACKING_TST = CLIENT["server_tracking_tst"]

import data_tracking

DEFAULT_SERVER = 1234


class ServerTest(object):
    def __init__(self, id):
        self.id = id


class MemberTest(object):
    def __init__(self, id, server):
        self.id = id
        self.name = "testmember"
        self.server = server

member = MemberTest(1003, ServerTest(1234))
x = data_tracking.MemberDocument(member, db=SERVER_TRACKING_TST)
x.disconnection()
time.sleep(10)
x.connection()

print(x.total_connection_time())

