from datetime import datetime
from dotenv import load_dotenv
import json
from pymongo import MongoClient
import os

load_dotenv("auth.env")
CLIENT = MongoClient(os.getenv("DISCORD_MONGO"))
SERVER_TRACKING = CLIENT["server_tracking"]
DATE_FORMAT = "dd/mm/yyyy"
TIME_FORMAT = "HH:MM:SS"


def new_server_collection(server):
    if server.id not in SERVER_TRACKING.collection_names():
        return SERVER_TRACKING[str(server.id)]


def insert_collection(func):
    def decorator(self, server, *args, **kwargs):
        new_server_collection(server)
        return func(self, server, *args, **kwargs)
    return decorator


class MemberDocument(object):

    @insert_collection
    def __init__(self, server, member):
        server_collection = SERVER_TRACKING[str(server.id)]
        document_search = list(server_collection.find({"user_id": member.id}))
        if document_search:
            document = document_search[0]
        else:
            now = datetime.now()
            document = {
                "id": str(member.id),
                "join_date": now.strftime("dd/mm/yyyy"),
                "join_time": now.strftime("HH:MM:SS"),
                "messages": list(),
                "server_connection": {
                    "connections": list(),
                    "disconnections": list()
                },
                "AFKs": {
                    "entrances": list(),
                    "exits": list()
                }
            }
            server_collection.insert_one(document)
        self.document = document
        self.id

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

    def _new_server_connection(self, connection_type, count):
        now = datetime.now()
        self.server_connections[connection_type].append({"date": now.strftime(DATE_FORMAT),
                                                         "time": now.strftime(TIME_FORMAT)})

    def _new_afk(self, afk_type, count):
        now = datetime.now()
        self.AFKs[afk_type].append({"date": now.strftime(DATE_FORMAT),
                                    "time": now.strftime(TIME_FORMAT)})

    def connection(self):
        self._new_server_connection("connections", self.server_connections_count)

    def disconnection(self):
        self._new_server_connection("disconnections", self.server_disconnections_count)

    def afk(self):
        self._new_afk("entrances", self.afk_entrances_count)

    def afk_exit(self):
        self._new_afk("exits", self.afk_exits_count)

    def message(self, text):
        now = datetime.now()
        self.messages.append({"date": now.strftime(DATE_FORMAT),
                              "time": now.strftime(TIME_FORMAT),
                              "text": text})
