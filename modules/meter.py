# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pytz
import pandas as pd

import threading
from threading import Event

from modules.helpers import Helper
from modules.database import Database
from modules.meterdata import GPdata

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from concurrent.futures import wait
from concurrent.futures import thread

# serial_nos = [ "40190029","43200016","40190085","52190205"]
# serial_nos = ["40190029", "40190085","40190591"]

IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.utc


class Meter(GPdata, Database, Helper):

    def __init__(self):

        super().__init__()

        self.select_machine = {"uat": "MongoDB_UAT", "dev": "MongoDB_DEV", "prod": "MongoDB_PROD"}
        self.results = pd.DataFrame()
        self.Ids = set()
        self.phases = ["r", "y", "b", "ry", "rb", "yb", "yr", "br", "by", "ryb", "ybr", "bry"]

    def run(self, meter_list, num_workers):
        try:
            s = []
            self.results = pd.DataFrame()

            fetch = self.fetchandparse

            # Create queue and add items

            today_IST = datetime.now(IST)
            today_UTC = datetime.now(UTC)

            endTime = today_UTC.replace(tzinfo=UTC).astimezone(IST)

            for meter in meter_list:
                serialNo = meter['serialNo']

                if "updatedAt_meterRaw" in meter:
                    try:
                        # startTime = meter["updatedAt_meterRaw"].replace(tzinfo=UTC)

                        # energy,kwh = self.get_previous( serialNo, startTime)

                        energy = meter["total_real_energy"]
                        kwh = meter["current_kwh"]

                        startTime = meter["updatedAt_meterRaw"].replace(tzinfo=UTC).astimezone(IST)
                        self.previous_kwh[serialNo] = {"energy": energy, "kwh": kwh, "time": startTime}
                    except Exception as err:
                        self.logger_err.error(err, exc_info=True)

                else:
                    # startTime = endTime - timedelta(days=1)
                    startTime = endTime.replace(hour=0, minute=0, second=0)
                    # startTime = endTime - timedelta(hours=3)
                    # startTime = datetime.combine(endTime,datetime.min.time()).astimezone(IST)

                    self.previous_kwh[serialNo] = {"energy": 0, "kwh": 0, "time": startTime}

                serial_no = serialNo.split('_')
                if len(serial_no) > 1:
                    GP_serialNo = serial_no[0]
                    phase = serial_no[1].lower()

                    if phase in self.phases:
                        s.append((serialNo, GP_serialNo, phase, startTime, endTime))
                    else:
                        log = f'Phase: {serialNo} incorrect'
                        self.logger_err.error(log)

                else:
                    log = f'Serial no: {serialNo} incorrect'
                    self.logger_err.error(log)

                # if GP_serialNo in serial_nos:

            with ThreadPoolExecutor(num_workers) as executor:

                try:
                    print("Starting threads")
                    futures = [executor.submit(fetch, serialNo, GP_serialNo, phase, startTime, endTime)
                               for serialNo, GP_serialNo, phase, startTime, endTime in s]
                    for future in as_completed(futures):

                        r = future.result()

                        if r is not None:
                            self.logger_info.info(r)

                        # data, s = future.result()
                        # if data is not None:

                        #     self.results = pd.concat([self.results, data])
                        #     r=f'Task={s}: Done'
                        #     self.logger_info.info(r)

                except KeyboardInterrupt:
                    self.logger_err.error("Keyboard Interrupt")
                    executor._threads.clear()
                    thread._threads_queues.clear()
                    raise

        except Exception as err:
            self.logger_err.error(err, exc_info=True)

    # def run_parse(self, data, num_workers, meters):
    #     try:

    #         parse = self.parseData

    #         s=[]

    #         for GP_serialNo, data_rec in data.items():
    #             serialNo = meters[GP_serialNo]["serialNo"]
    #             phase = meters[GP_serialNo]["phase"]
    #             data_rec = data_rec.to_dict('records')

    #             s.append((data_rec,serialNo, phase.lower()))

    #         with ThreadPoolExecutor(num_workers) as executor:

    #             try:

    #                 futures = [executor.submit(parse, data_rec,serialNo, phase) 
    #                            for data_rec, serialNo, phase in s]
    #                 for future in as_completed(futures):
    #                     r = future.result()

    #                     if r is not None:
    #                         self.logger_info.info(r)

    #             except KeyboardInterrupt:
    #                 self.logger_err.error("Keyboard Interrupt")
    #                 executor._threads.clear()
    #                 thread._threads_queues.clear()
    #                 raise

    #     except Exception as err:
    #         self.logger_err.error(err,exc_info=False)

    def closelog(self):
        try:
            handlers = self.logger1.handlers[:]
            for handler in handlers:
                self.logger1.removeHandler(handler)
                handler.close()

            handlers = self.logger2.handlers[:]
            for handler in handlers:
                self.logger2.removeHandler(handler)
                handler.close()
        except Exception as err:
            self.logger_err.error(err, exc_info=False)
