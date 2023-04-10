import time
import requests
from SMCApi.Grievance import Grievance
from Core.Logger import Logger
from os import path, makedirs, listdir, rename
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from xml.dom.minidom import parse


class Runner:
    def __init__(self, **kwargs):
        self._settings_file = kwargs.get('settings', 'grievance.ini')
        self._output_folder = ""
        self._cases_folder = ""
        self._cases = {}
        self._reservations = {}
        self._telegram_channel = ""
        self._telegram_bot = ""
        self._sleep = 0
        self._threads_count = 0
        self._logger = kwargs.get('logger', Logger(debug=True))

    def readSettings(self):
        self._logger.log(f"Trying to read {self._settings_file}")
        if not path.exists(self._settings_file):
            self._logger.log(f"{self._settings_file} can't be found in path")
            return False
        config = ConfigParser()
        config.read(self._settings_file)
        self._telegram_bot = config.get("SETTINGS", "TELEGRAM_BOT")
        self._telegram_channel = config.get("SETTINGS", "TELEGRAM_CHANNEL")
        self._sleep = config.getint("SETTINGS", "SLEEP")
        self._cases_folder = config.get("SETTINGS", "CASES_FOLDER")
        self._output_folder = config.get("SETTINGS", "FINISHED_FOLDER")
        self._threads_count = config.getint('SETTINGS', "THREADS_COUNT")

    def readCasesFolder(self):
        self._logger.log(f"Trying to read {self._cases_folder}")
        for cases_sub_dir in listdir(self._cases_folder):
            cases_sub_folder = path.join(self._cases_folder, cases_sub_dir)
            self._cases[cases_sub_dir] = {}
            for case_file in listdir(cases_sub_folder):
                case_xml = parse(path.join(cases_sub_folder, case_file))
                case_dict = {
                    "ssn": case_xml.getElementsByTagName("ssn")[0].firstChild.nodeValue,
                    "council_name": case_xml.getElementsByTagName("council")[0].firstChild.nodeValue,
                    "note": case_xml.getElementsByTagName("note")[0].firstChild.nodeValue,
                    "ddl": []
                }

                for ddl in case_xml.getElementsByTagName("ddl")[0].getElementsByTagName("option"):
                    if ddl.getAttribute("checked") == "1":
                        case_dict['ddl'].append(ddl.getAttribute("value"))

                self._cases[cases_sub_dir][case_file] = case_dict

    def sendMessage(self, message):
        self._logger.log("Trying to send message to telegram")
        requests.get(f'https://api.telegram.org/bot{self._telegram_bot}/sendMessage',
                     params={
                         'chat_id': self._telegram_channel,
                         'text': message
                     })

    def reservation(self, country, case_file, **kwargs):
        if f'{country}-{case_file}' not in self._reservations:
            self._reservations[f'{country}-{case_file}'] = Grievance(**kwargs, logger=self._logger)
        reservation_thread: Grievance = self._reservations[f'{country}-{case_file}']

        if reservation_thread.stage == 0:
            if not reservation_thread.submitSSN():
                del self._reservations[f'{country}-{case_file}']
                return

        if not kwargs.get("reserve"):
            self._logger.log(f"{country} -> {case_file} Started")
            return

        if reservation_thread.stage == 1:
            reservation_thread.submitCouncil()

        if reservation_thread.stage == 2:
            reservation_thread.submitDate()

        if reservation_thread.stage == 3:
            self._logger.log("Reservation Started")
            time.sleep(time.time() - reservation_thread.start_time) \
                if 0 < time.time() - reservation_thread.start_time < 60 * 1.5 else None
            reservation_thread.submitTime()

        if reservation_thread.done:
            del self._reservations[f'{country}-{case_file}']
            makedirs(path.join(self._output_folder, country), exist_ok=True)
            rename(path.join(self._cases_folder, country, case_file),
                   path.join(self._output_folder, country, case_file))
            self.sendMessage(f"""
                                تم تظلم حاله كرامة
                                رقم البطاقة: {kwargs.get("ssn")}
                            """ + f"""ملاحظه: {kwargs.get("note")}""" if kwargs.get("note") else "")
            del self._cases[country][case_file]
            del self._reservations[f'{country}-{case_file}']

    def run(self):
        self._logger.log("Reservation Process Started")
        while True:
            with ThreadPoolExecutor(self._threads_count) as e:
                for country, cases in self._cases.items():
                    for case_file, case_info in cases.items():
                        e.submit(self.reservation, country, case_file, **case_info, reserve=False)

            with ThreadPoolExecutor(self._threads_count) as e:
                for reservation_thread in self._reservations:
                    country, case_file = reservation_thread.split('-')
                    e.submit(self.reservation, country, case_file, **case_info, reserve=True)

            if not self._reservations:
                input("Completed")
                runner.readSettings()
                runner.readCasesFolder()


if __name__ == "__main__":
    runner = Runner()
    runner.readSettings()
    runner.readCasesFolder()
    runner.run()