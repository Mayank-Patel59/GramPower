# -*- coding: utf-8 -*-

import os
import sys
import math
import pandas as pd
import time
import threading, queue
from datetime import datetime, timedelta
import pytz
import modules as m

IST = pytz.timezone('Asia/Kolkata')  # Set default timezone as IST
UTC = pytz.utc  # Set UTC timezone because dbb have data in UTC


def main():
    minutes = 5  # set Timer for 5 min where script will be run
    try:
        meter_list = []  # Created meter_list list variable
        df_groups = None  # Defined dataframe group
        GP_meter = m.Meter()  # meter object

        config1 = GP_meter.read_config()  # Config file
        machine = GP_meter.select_machine[config1["AWS"]["machine"]]  # Cloud server Config

        # Database details
        MongoDB_Host = config1[machine]["HOST"]  # Connection of Mongodb
        MongoDB_port = int(config1[machine]["PORT"])  # Server Port Connection
        dbname = config1[machine]["DB"]  # DB name
        collname = config1[machine]["deviceMap"]  # Db Collection Name
        meterRaw_name = config1[machine]["meterRaw_name"]  # Database name

        # meterRaw schema
        schema = GP_meter.get_Schema()  # Getting schema from the mererRaw
        GP_meter.clean(schema["required"])  # Cleaning the data from meterRaw

        run = True

        while run:
            try:
                # Getting Db values from the function
                GP_meter.connect_db(MongoDB_Host, MongoDB_port, dbname, collname, meterRaw_name)
                meter_list = GP_meter.get_meters()

                # meters={}
                # for meter in meter_list:
                #     serialNo = meter['serialNo']
                #     GP_serialNo,phase = serialNo.split('_')

                #     meters[GP_serialNo]={"serialNo":serialNo,"phase":phase}

                start_time = time.time()  # Taking Start time in Seconds

                num_workers = math.ceil(
                    len(meter_list) / 5)  # Calculating divide operation & round by nearest up values

                # GP_meter.run_fetch(meter_list,num_workers)

                GP_meter.run(meter_list, num_workers)  # Time Taken by gp_meter in seconds
                # print("Fetching Time taken %s seconds" % (time.time() - start_time))

                # s = f'---- Fetching Time taken = {time.time() - start_time} seconds ----'
                # GP_meter.logger_info.info(s)

                # Checking condition for values should not be empty
                if not GP_meter.results.empty:
                    df = GP_meter.results.groupby('serial_no')  # Fetching result base on SerialNo
                    df_groups = dict(list(df))  # Grouping by using Dataframe

                    # start_time = time.time()

                    # GP_meter.run_parse(df_groups,num_workers,meters)

                    print("Fetching and Parsing Time taken %s seconds " % (
                                time.time() - start_time))  # Time Taken by gp_meter in seconds
                    s = f'---- Fetching and Parsing Time taken = {time.time() - start_time} seconds ----'
                    GP_meter.logger_info.info(s)  # If there is any error it will create log of error & save
                else:
                    s = f'---- No Data fetched, Time taken = {time.time() - start_time} seconds ----'  # Time Taken
                    # by gp_meter in seconds
                    GP_meter.logger_info.info(s)  # If there is any error it will create log of error & save

                new_start = time.time()  # Taking new_start in seconds
                while time.time() - new_start < minutes * 60:  # If time is less than seconds
                    time.sleep(1)  # Add delay in the execution of a program.

            # GP_meter.meterRaw.insert_many(GP_meter.results)
            # df = pd.DataFrame(GP_meter.results)  

            # latest = GP_meter.results.groupby('serialNo')['updatedAt'].max().to_dict()

            # GP_meter.updateTimestamp_many(latest)
            # return meter_list,GP_meter.results,df_groups

            except Exception as err:  # Exception Handling
                run = False
                GP_meter.logger_err.error(err, exc_info=True)

                return meter_list, GP_meter.results, df_groups

        GP_meter.closelog()

    except Exception as err:

        GP_meter.logger_err.error(err, exc_info=True)

        return meter_list, GP_meter.results, df_groups

    except KeyboardInterrupt as err:
        GP_meter.logger_err.error(err, exc_info=True)

        return meter_list, GP_meter.results, df_groups


if __name__ == "__main__":

    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Directory Path

        print(os.getcwd())

        l, rlist, r = main()
        # main()
        print("Program Running complete")

    except KeyboardInterrupt as e:
        print("Stopped", e)
