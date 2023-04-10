import time
import requests
from SMCApi.Reservation import Reservation
from Core.Logger import Logger
from os import path, makedirs, listdir, rename
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from xml.dom.minidom import parse


class Runner:
    def __init__(self, **kwargs):
        self._settings_file = kwargs.get('settings', 'register.ini')
        self._output_folder = ""
        self._cases_folder = ""
        self._telegram_channel = ""
        self._telegram_bot = ""
        self._sleep = 0
        self._threads_count = 0
        self._logger = kwargs.get('logger', Logger(debug=True))
        self._cases = {}
        self._reservations = {}

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
                    "first_name": case_xml.getElementsByTagName("firstName")[0].firstChild.nodeValue,
                    "second_name": case_xml.getElementsByTagName("secondName")[0].firstChild.nodeValue,
                    "third_name": case_xml.getElementsByTagName("thirdName")[0].firstChild.nodeValue,
                    "fourth_name": case_xml.getElementsByTagName("fourthName")[0].firstChild.nodeValue,
                    "phone_number": case_xml.getElementsByTagName("phoneNumber")[0].firstChild.nodeValue,
                    "note": case_xml.getElementsByTagName("note")[0].firstChild.nodeValue,
                    "governorate": "",
                    "city": case_xml.getElementsByTagName("city")[0].firstChild.nodeValue,
                    "address": case_xml.getElementsByTagName("address")[0].firstChild.nodeValue,
                    "martial_status": "",
                    "job": "",
                    "ddl": []
                }

                for governorate in case_xml.getElementsByTagName("governorate")[0].getElementsByTagName("option"):
                    if governorate.getAttribute("checked") == "1":
                        case_dict['governorate'] = governorate.getAttribute("value")
                        break

                for marital_status in case_xml.getElementsByTagName("MaritalStatus")[0].getElementsByTagName("option"):
                    if marital_status.getAttribute("checked") == "1":
                        case_dict['martial_status'] = marital_status.getAttribute("value")
                        break

                for job in case_xml.getElementsByTagName("Job")[0].getElementsByTagName("option"):
                    if job.getAttribute("checked") == "1":
                        case_dict['job'] = job.getAttribute("value")
                        break

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
        self._logger.log(message)

    def done(self, country, case_file):
        del self._reservations[f'{country}-{case_file}']
        del self._cases[country][case_file]
        makedirs(path.join(self._output_folder, country), exist_ok=True)
        rename(path.join(self._cases_folder, country, case_file),
               path.join(self._output_folder, country, case_file))

    def reservation(self, country, case_file, **kwargs):
        if f'{country}-{case_file}' not in self._reservations:
            self._reservations[f'{country}-{case_file}'] = Reservation(**kwargs, logger=self._logger)
        reservation_thread: Reservation = self._reservations[f'{country}-{case_file}']
        if reservation_thread.stage == 0:
            if not reservation_thread.submitSSN():
                self.done(country, case_file)
                return

        if reservation_thread.stage == 1:
            if not reservation_thread.submitGovernorate():
                self.done(country, case_file)
                return

        if reservation_thread.stage == 2:
            if not reservation_thread.submitCouncil():
                self._reservations[f'{country}-{case_file}'] = Reservation(**kwargs, logger=self._logger)
                return self.reservation(country, case_file, **kwargs)

        if not kwargs.get("reserve"):
            self._logger.log(f"{country} -> {case_file} Started")
            return

        if reservation_thread.stage == 3:
            reservation_thread.submitDate()

        if reservation_thread.stage == 4:
            time.sleep(time.time() - reservation_thread.start_time)\
                if 0 < time.time() - reservation_thread.start_time < 60*1.5 else None
            reservation_thread.submitTime()

        if reservation_thread.done:
            note = f'ملاحظه: {kwargs.get("note")}' if kwargs.get('note') else ''
            self.sendMessage(f"""
                                تم حجز حاله كرامة
                                الاسم: {kwargs.get("first_name")} {kwargs.get("second_name")} {kwargs.get("third_name")} {kwargs.get("fourth_name")}
                                رقم البطاقة: {kwargs.get("ssn")}
                                رقم الموبيل: {kwargs.get("phoneNumber")}
                                طلب الحاله: {reservation_thread.request_url}
                                {note}
                            """)
            self.done(country, case_file)

    def run(self):
        self._logger.log("Reservation Process Started")
        while True:
            with ThreadPoolExecutor(self._threads_count) as e:
                for country, cases in self._cases.items():
                    for case_file, case_info in cases.items():
                        e.submit(self.reservation, country, case_file, **case_info, reserve=False)

                for reservation_thread in self._reservations:
                    e.submit(self.reservation, *reservation_thread.split('-'), **case_info, reserve=True)

            if not self._reservations:
                runner.readSettings()
                runner.readCasesFolder()


if __name__ == "__main__":
    runner = Runner()
    runner.readSettings()
    runner.readCasesFolder()
    runner.run()