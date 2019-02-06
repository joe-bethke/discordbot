from datetime import datetime
from dateutil.relativedelta import relativedelta
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
        """Number of times the Member has connected to the server"""
        return len(self.server_connections.get("connections", list()))

    @property
    def server_disconnections_count(self):
        """Number of times the Member has disconnected from the server"""
        return len(self.server_connections.get("disconnections", list()))

    @property
    def afk_entrances_count(self):
        """Number of times the Member has entered the AFK channel"""
        return len(self.AFKs.get("entrances", list()))

    @property
    def afk_exits_count(self):
        """Number of times the Member has exitted the AFK channel"""
        return len(self.AFKs.get("exits", list()))

    @property
    def message_count(self):
        """Number of messages sent by the Member"""
        return len(self.messages)

    @_update_doc
    def _new_server_connection(self, connection_type):
        """Update the MemberDocument in the MongoDB with a new server connection entry"""
        now = datetime.now()
        connection = {
            "date": now.strftime(DATE_FORMAT),
            "time": now.strftime(TIME_FORMAT)
        }
        self.server_connections[connection_type].append(connection)
        return {"$push": {"server_connections.{}".format(connection_type): connection}}

    @_update_doc
    def _new_afk(self, afk_type):
        """Update the MemberDocument in the MongoDB with a new AFK entry"""
        now = datetime.now()
        afk = {
            "date": now.strftime(DATE_FORMAT),
            "time": now.strftime(TIME_FORMAT)
        }
        self.AFKs[afk_type].append(afk)
        return {"$push": {"AFKs.{}".format(afk_type): afk}}

    def _timestamps_to_datetime(self, *args):
        """
        return a datetime instance for each time stamp passed to this function
        timestamps should be a full server connection or afk entry
        """

        time_parse = "{} {}".format(DATE_FORMAT, TIME_FORMAT)
        return tuple([datetime.strptime("{date} {time}".format(**timestamp), time_parse) for timestamp in args])

    def _server_connection_by_index(self, index):
        """get datetime instances for the server connection entries at the given index"""
        if index < self.server_connections_count and index < self.server_disconnections_count:
            dc = self.server_connections['disconnections'][index]
            connection = self.server_connections['connections'][index]
            return self._timestamps_to_datetime(dc, connection)
        else:
            raise ValueError("The given index exceeds the connection or disconnection count of this MemberDocument.")

    def _afks_by_index(self, index):
        """get datetime instances for the afk entries at the given index"""
        if index < self.afk_entrances_count and index < self.afk_exits_count:
            afk = self.AKFs['entrances'][index]
            connection = self.AFKs['exits'][index]
            return self._timestamps_to_datetime(afk, connection)
        else:
            raise ValueError("The given index exceeds the afk entrance or exit count of this MemberDocument.")

    def connection(self):
        """Create a new connection entry in the MemberDocument"""
        self._new_server_connection("connections")

    def disconnection(self):
        """Create a new disconnection entry in the MemberDocument"""
        self._new_server_connection("disconnections")

    def afk(self):
        """Create a new afk entry in the MemberDocument"""
        self._new_afk("entrances")

    def afk_exit(self):
        """Create a new afk exit entry in the MemberDocument"""
        self._new_afk("exits")

    @_update_doc
    def message(self, text):
        """Create a new message entry in the MemberDocument"""
        now = datetime.now()
        message = {
            "date": now.strftime(DATE_FORMAT),
            "time": now.strftime(TIME_FORMAT),
            "text": text
        }
        self.messages.append(message)
        return {"$push": {"messages": message}}

    def total_connection_time(self):
        try:
            first_conn, first_dc = self._server_connection_by_index(0)
            server_disconnection_start = 0 if first_conn >= first_dc else 1  # If True, count the first disconnection
            last_conn, last_dc = self._server_connection_by_index(-1)
            server_connection_end = self.server_connections_count
        except ValueError:
            return ("Unable to calculate Member's connection time." +
                    "But, I can say that they've probably spent way too much time playing games with their friends")
        if last_dc > last_conn:
            # do not count the last connection
            server_connection_end -= 1
        total_time = relativedelta()
        for server_connection_index in range(server_disconnection_start, server_connection_end):
            connection, dc = self._server_connection_by_index(server_connection_index)
            total_time += relativedelta(connection, dc)
        total_connection_string = ", ".join("{} {}".format(str(getattr(total_time, time_attr)), time_attr)
                                            for time_attr in ('years', 'months', 'days', 'hours', 'minutes', 'seconds'))
        return "{u} has been connected to the server for {t}".format(u=self.username, t=total_connection_string)
