from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv("auth.env")
CLIENT = MongoClient(os.getenv("DISCORD_MONGO"))
SERVER_TRACKING = CLIENT["server_tracking"]
DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M:%S"


def _update_doc(func):
    def mongo_update(self, *args, **kwargs):
        update = func(self, *args, **kwargs)
        self.server_collection.update_one({"id": self.id}, update)
        return
    return mongo_update


class MemberDocument(object):

    def __init__(self, member, db=SERVER_TRACKING):
        self.server_collection = db[str(member.server.id)]
        document_search = list(self.server_collection.find({"id": member.id}))
        if document_search:
            # Document & member already exist
            document = document_search[0]
        else:
            # create new member document
            now = datetime.now()
            document = {
                "id": member.id,
                "username": member.name,
                "join_date": now.strftime(DATE_FORMAT),
                "join_time": now.strftime(TIME_FORMAT),
                "messages": list(),
                "server_connections": {
                    "connections": list(),
                    "disconnections": list()
                },
                "AFKs": {
                    "entrances": list(),
                    "exits": list()
                }
            }
            self.server_collection.insert_one(document)
        self.document = document
        self.server = member.server
        self.discord = member

    def __getitem__(self, key):
        return self.document[key]

    def __getattr__(self, name):
        return self.document[name]

    def __repr__(self):
        return str(self.document)

    def __str__(self):
        return self.__repr__()

    @property
    def server_connections_count(self):
        return len(self.server_connections.get("connections", list()))

    @property
    def server_disconnections_count(self):
        return len(self.server_connections.get("disconnections", list()))

    @property
    def afk_entrances_count(self):
        return len(self.AFKs.get("entrances", list()))

    @property
    def afk_exits_count(self):
        return len(self.AFKs.get("exits", list()))

    @property
    def message_count(self):
        return len(self.messages)

    @_update_doc
    def _new_server_connection(self, connection_type, count):
        now = datetime.now()
        connection = {
            "date": now.strftime(DATE_FORMAT),
            "time": now.strftime(TIME_FORMAT)
        }
        self.server_connections[connection_type].append(connection)
        return {"$push": {"server_connections.{}".format(connection_type): connection}}

    @_update_doc
    def _new_afk(self, afk_type, count):
        now = datetime.now()
        afk = {
            "date": now.strftime(DATE_FORMAT),
            "time": now.strftime(TIME_FORMAT)
        }
        self.AFKs[afk_type].append(afk)
        return {"$push": {"AFKs.{}".format(afk_type): afk}}

    def connection(self):
        self._new_server_connection("connections", self.server_connections_count)

    def disconnection(self):
        self._new_server_connection("disconnections", self.server_disconnections_count)

    def afk(self):
        self._new_afk("entrances", self.afk_entrances_count)

    def afk_exit(self):
        self._new_afk("exits", self.afk_exits_count)

    @_update_doc
    def message(self, text):
        now = datetime.now()
        message = {
            "date": now.strftime(DATE_FORMAT),
            "time": now.strftime(TIME_FORMAT),
            "text": text
        }
        self.messages.append(message)
        return {"$push": {"messages": message}}
