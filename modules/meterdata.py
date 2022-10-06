# -*- coding: utf-8 -*-

import logging

from datetime import datetime, timedelta
import pytz

import requests
import pandas as pd

from modules.loggers import Loggers
from modules.database import Database

IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.utc

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/39.0.2171.95 Safari/537.36",
    "Authorization": "Api-Key hWpbOKwr.K3tZ37E1qbJd9ATPkkK3MZS1Yq59e6lf",
    "Content-Type": "application/json"}
data_format = '{{ "serial_no": "{0}", "start_time": "{1}", "end_time": "{2}" }}'
url = "https://api.grampower.com/gp_api/panel-wifi-raw-export"


class GPdata(Database, Loggers):

    def __init__(self):
        super().__init__()
        name = __class__.__name__

        extra = {'className': name}

        self.logger_info = logging.LoggerAdapter(self.logger1, extra)

        self.logger_err = logging.LoggerAdapter(self.logger2, extra)

        self.meterRaw_doc = {}
        self.doc = None

        self.gp_keys_curr = {"r": "r_phase_current", "y": "y_phase_current", "b": "b_phase_current"}
        self.gp_keys_pf = {"r": "r_phase_pf", "y": "y_phase_pf", "b": "b_phase_pf"}
        self.gp_keys_volt = {"r": "r_phase_voltage", "y": "y_phase_voltage", "b": "b_phase_voltage"}

        self.previous_kwh = {}

        self.Ids = set()

        self.GP_keys = {'y_phase_voltage': 250.33, 'y_phase_current': 5.91, 'y_phase_pf': 0.68,
                        'b_phase_voltage': 250.01, 'b_phase_current': 5.41, 'b_phase_pf': 0.72,
                        'r_phase_voltage': 249.05, 'r_phase_current': 7.78, 'r_phase_pf': 0.79,
                        'total_reactive_power': 3211.73, 'total_reactive_energy': 4931.83,
                        'total_apparent_energy': 9314.27, 'total_real_energy': 7846.48,
                        'serial_no': '46030017', 'timestamp': '2022-07-14 04:18:08',
                        'total_active_power': 3507.35, 'total_apparent_power': 4768.92,
                        'frequency': 49.97, 'total_pf': 0.74, }

    def fetch_loop(self, sess, results, serialNo, GP_serialNo, time_start):

        try:

            for i in range(len(time_start) - 1):

                st = time_start[i]
                et = time_start[i + 1]

                response = sess.post(url, headers=headers, data=data_format.format(GP_serialNo, st, et))
                response.raise_for_status()

                if response.ok:

                    parsed = response.json()

                    if "data" in parsed:

                        s = f'Data received for : {serialNo} , start:' + st + "  end: " + et + " "

                        self.logger_info.info(s)

                        data_rec = parsed['data']
                        data_rec = sorted(data_rec, key=lambda d: d['timestamp'])

                        data_rec = pd.DataFrame(data_rec)
                        results = pd.concat([results, data_rec])
                    else:
                        s = f'No Data for : {serialNo} , start:' + st + "  end: " + et

                        self.logger_info.info(s)

            return results

        except requests.exceptions.RequestException as err:

            err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
            self.logger_err.error(err_str, exc_info=True)
            return results

        except Exception as err:
            err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
            self.logger_err.error(err_str, exc_info=True)
            return results

    def fetchData(self, serialNo, GP_serialNo, phase, startTime, endTime):

        try:
            # thread = current_thread()

            # self.Ids.add(f'Thread: name={thread.name}, idnet={get_ident()}, id={get_native_id()}')

            s = f'Thread Started: API request for : {serialNo} '

            self.logger_info.info(s)

            sess = requests.Session()

            results = pd.DataFrame()

            if endTime - startTime >= timedelta(minutes=30):
                print("more than 30 mins")

                time_start = (
                    pd.DataFrame(columns=['NULL'], index=pd.date_range(startTime, endTime, freq='30T'))).index.tolist()
                if time_start[-1] != endTime:
                    time_start.append(endTime)

                time_start = [i.strftime('%Y-%m-%d %H:%M:%S') for i in time_start]

                try:

                    for i in range(len(time_start) - 1):

                        st = time_start[i]
                        et = time_start[i + 1]

                        response = sess.post(url, headers=headers, data=data_format.format(GP_serialNo, st, et))
                        response.raise_for_status()

                        if response.ok:

                            parsed = response.json()

                            if "data" in parsed:

                                s = f'Data received for : {serialNo} , start:' + st + "  end: " + et + " "

                                self.logger_info.info(s)

                                data_rec = parsed['data']
                                data_rec = sorted(data_rec, key=lambda d: d['timestamp'])

                                data_rec = pd.DataFrame(data_rec)
                                results = pd.concat([results, data_rec])
                            else:
                                s = f'No Data for : {serialNo} , start:' + st + "  end: " + et

                                self.logger_info.info(s)

                    return results, serialNo

                except requests.exceptions.RequestException as err:

                    err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
                    self.logger_err.error(err_str, exc_info=True)
                    return results, serialNo

                except Exception as err:
                    err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
                    self.logger_err.error(err_str, exc_info=True)
                    return results, serialNo

            else:
                try:

                    print("less than 30 mins")
                    st = startTime.strftime('%Y-%m-%d %H:%M:%S')
                    et = endTime.strftime('%Y-%m-%d %H:%M:%S')
                    response = sess.post(url, headers=headers, data=data_format.format(GP_serialNo, st, et))
                    response.raise_for_status()

                    if response.ok:
                        parsed = response.json()

                        if "data" in parsed:

                            s = f'Data received for : {serialNo} , start:' + st + "  end: " + et

                            self.logger_info.info(s)

                            data_rec = parsed['data']
                            data_rec = sorted(data_rec, key=lambda d: d['timestamp'])
                            data_rec = pd.DataFrame(data_rec)
                            results = pd.concat([results, data_rec])

                        else:
                            s = f'No Data for : {serialNo} , start:' + st + "  end: " + et

                            self.logger_info.info(s)

                    return results, serialNo

                except requests.exceptions.RequestException as err:
                    err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
                    self.logger_err.error(err_str, exc_info=True)
                    return results, serialNo

                except Exception as err:
                    err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
                    self.logger_err.error(err_str, exc_info=True)
                    return results, serialNo

        except Exception as err:
            err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
            self.logger_err.error(err_str, exc_info=True)
            return results, serialNo

    def parseData(self, data_rec, serialNo, phase, GP_serialNo):

        try:
            # thread = current_thread()

            # self.Ids.add(f'Thread: name={thread.name}, idnet={get_ident()}, id={get_native_id()}')

            s = f'Thread Started: Pushing data to DB for : {serialNo}'

            self.logger_info.info(s)

            n = dir(self.doc)
            time_prev = self.previous_kwh[serialNo]["time"]
            energy_prev = self.previous_kwh[serialNo]["energy"]
            kwh_prev = self.previous_kwh[serialNo]["kwh"]
            kwh_curr = kwh_prev

            for data in data_rec:
                if str(data["serial_no"]) != str(GP_serialNo):
                    err_str = f"Thread Error:  Serial no not matching: {serialNo} "
                    self.logger_err.error(err_str, exc_info=True)


                elif str(data["serial_no"]) == str(GP_serialNo):
                    try:

                        new_dict = {}

                        energy_curr = data["total_real_energy"]
                        time_now = datetime.strptime(data["timestamp"], '%Y-%m-%d %H:%M:%S').astimezone(IST)

                        if time_now > time_prev and (time_now - time_prev <= timedelta(minutes=20)):
                            if time_prev.date() == time_now.date():

                                if energy_prev != 0 and (energy_curr >= energy_prev):

                                    diff = (energy_curr - energy_prev)
                                    if kwh_prev != None:

                                        kwh_curr = kwh_prev + diff
                                    else:
                                        kwh_curr = diff


                                else:
                                    kwh_curr = kwh_prev
                            else:
                                kwh_curr = 0

                        time_prev = time_now
                        energy_prev = energy_curr
                        kwh_prev = kwh_curr

                    except Exception as err:
                        e = f"{serialNo} error in calculation current kwh" + str(err)
                        self.logger_err.error(e, exc_info=True)

                    self.doc.current_kwh = kwh_curr
                    self.doc.updatedAt = datetime.strptime(data["timestamp"], '%Y-%m-%d %H:%M:%S').astimezone(UTC)

                    self.doc.serialNo = serialNo
                    self.doc.createdAt = datetime.now().astimezone(UTC)

                    if len(phase) == 1:
                        self.doc.Current = data[self.gp_keys_curr[phase]]
                        self.doc.power_factor = data[self.gp_keys_pf[phase]]
                        self.doc.Voltage = data[self.gp_keys_volt[phase]]
                        self.doc.PowerW = self.doc.Current * self.doc.power_factor * self.doc.Voltage


                    elif len(phase) == 2 or len(phase) == 3:
                        self.doc.PowerW = data["total_active_power"]

                        curr = []
                        pf = []
                        volt = []
                        for p in phase:
                            curr.append(data[self.gp_keys_curr[p]])
                            pf.append(data[self.gp_keys_pf[p]])
                            volt.append(data[self.gp_keys_volt[p]])

                        self.doc.Current = curr
                        self.doc.power_factor = pf
                        self.doc.Voltage = volt

                    for k, v in self.meterRaw_doc.items():
                        # print(k)
                        # print(v)

                        if v in n:
                            # print(self.doc.__getattribute__(v))
                            new_dict[k] = self.doc.__getattribute__(v)
                            self.doc.__setattr__(v, None)

                    new_dict["total_real_energy"] = data["total_real_energy"]

                    self.meterRaw.update_one({"serialNo": new_dict["serialNo"], "updatedAt": new_dict["updatedAt"]},
                                             {"$setOnInsert": new_dict}, upsert=True)

                    # self.deviceMap.update_one({"serialNo":new_dict["serialNo"]},{"$set":{"updatedAt_meterRaw":new_dict["updatedAt"]}})
                    self.updateTimestamp_one(new_dict["serialNo"], new_dict["updatedAt"], data["total_real_energy"],
                                             new_dict["current_kwh"])

            return f'Parse Task={serialNo}: Done'




        except Exception as err:
            err_str = f"Thread Error:  Serial no : {serialNo} " + str(err)
            self.logger_err.error(err_str, exc_info=True)
            return None

    def fetchandparse(self, serialNo, GP_serialNo, phase, startTime, endTime):
        r = None

        data, s = self.fetchData(serialNo, GP_serialNo, phase, startTime, endTime)
        # print(data)
        logs = f'Fetch Task={s}: Done'
        self.logger_info.info(logs)

        if not data.empty:
            self.results = pd.concat([self.results, data])
            data = data.to_dict('records')

            r = self.parseData(data, serialNo, phase, GP_serialNo)

        return r
