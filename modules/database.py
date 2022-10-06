# -*- coding: utf-8 -*-

import logging

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from modules.loggers import Loggers


class Database(Loggers):

    def __init__(self):
        super().__init__()
        name = __class__.__name__

        extra = {'className': name}

        self.logger_info = logging.LoggerAdapter(self.logger1, extra)

        self.logger_err = logging.LoggerAdapter(self.logger2, extra)

        self.db = None
        self.deviceMap = None
        self.meterRaw = None

    def connect_db(self, MongoDB_Host, MongoDB_port, dbname, collname, meterRaw_name):
        client = MongoClient(host=MongoDB_Host, port=MongoDB_port)
        try:
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ping')

            self.logger_info.info("Connection to MongoDB instance established")
            # print("Connection to MongoDB instance established")

            self.db = client[dbname]
            # self.logger_info.info(self.db.list_collection_names())
            # print(self.db.list_collection_names())

            self.deviceMap = self.db[collname]
            self.meterRaw = self.db[meterRaw_name]

        except ConnectionFailure as e:

            self.logger_err.error('Failed to establish connection to MongoDB instance ' + str(e), exc_info=False)
            # print("Failed to establish connection to MongoDB instance ")

    def get_meters(self):

        meter_list = []

        find_meters = {"Meter": "GramPower", "site_status": "live"}

        meter_list = list(self.deviceMap.find(find_meters))

        return meter_list

    def get_previous(self, serialNo, updatedAt_meterRaw):

        previous_kwh = 0
        previous_energy = 0
        find_latest = {"serialNo": serialNo, "updatedAt": updatedAt_meterRaw}

        previous = self.meterRaw.find_one(find_latest)
        if previous is not None:
            # print(previous)
            previous_energy = previous["total_real_energy"]
            previous_kwh = previous["current_kwh"]

        return previous_energy, previous_kwh

    def updateTimestamp_many(self, latest):

        for k, v in latest.items():
            self.deviceMap.update_one({"serialNo": k}, {"$set": {"updatedAt_meterRaw": v}})

    def updateTimestamp_one(self, serialNo, latestTime, energy, kwh):

        d = {"updatedAt_meterRaw": latestTime,
             "total_real_energy": energy,
             "current_kwh": kwh}

        self.deviceMap.update_one({"serialNo": serialNo}, {"$set": d})
