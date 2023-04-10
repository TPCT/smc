import time

import requests
from SMCApi.Notification import Notification
from Core.Logger import Logger
from os import path
from concurrent.futures import ThreadPoolExecutor


class Runner:
    def __init__(self, **kwargs):
        self._settings_file = kwargs.get('settings', 'notifications.ini')
        self._output_file = kwargs.get('output', 'notifications.txt')
        self._required_governorates = {}
        self._telegram_channel = ""
        self._telegram_bot = ""
        self._get_time = 1
        self._sleep = 0
        self._logger = kwargs.get('logger', Logger(debug=False))
        self._available_dates = {}

    def readSettings(self):
        self._logger.log(f"Trying to read {self._settings_file}")
        if not path.exists(self._settings_file):
            self._logger.log(f"{self._settings_file} can't be found in path")
            return False
        with open(self._settings_file, 'r+') as settings_reader:
            section = ""
            for line in settings_reader:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('[') and line.endswith(']'):
                    section = line.replace('[', '').replace(']', '')
                    continue
                if section == 'CITIES':
                    city_name, enabled = line.split('=')
                    if int(enabled.strip()):
                        self._required_governorates[city_name.strip()] = ""
                elif section == "SETTINGS":
                    if line.startswith('TELEGRAM_BOT'):
                        self._telegram_bot = line.split('=')[-1].strip()
                        continue
                    if line.startswith('TELEGRAM_CHANNEL'):
                        self._telegram_channel = line.split('=')[-1].strip()
                        continue
                    if line.startswith('SLEEP'):
                        self._sleep = line.split('=')[-1].strip()
                        continue
                    if line.startswith('GET_TIME'):
                        self._get_time = int(line.split('=')[-1].strip())
                        continue

    def sendMessage(self, message):
        self._logger.log("Trying to send message to telegram")
        with self._logger.lock, open(self._output_file, 'w+') as message_writer:
            requests.get(f'https://api.telegram.org/bot{self._telegram_bot}/sendMessage',
                         params={
                             'chat_id': self._telegram_channel,
                             'text': message
                         })
            message_writer.write(message)

    def appointmentThread(self, governorate_name, governorate_id):
        api = Notification(logger=self._logger)
        api.getCountries()
        api.getCity(governorate_id)
        for council_name, council_id in api.getCouncil(governorate_id).items():
            message = ""
            dates = api.getAppointmentDate(governorate_id, council_id)
            for date_name, date_id in dates.items():
                if not self._available_dates.get(date_id):
                    self._available_dates[date_id] = []
                    times = api.getAppointmentTime(governorate_id, council_id, date_id)

                    if not times:
                        continue
                    message = f"اشعار كرامة {governorate_name} {council_name}" if not message else message

                    message += f"\n\t\t{date_name.replace(' ', '')}"
                    if self._get_time:
                        for time_name, time_id in times.items():
                            if time_id not in self._available_dates[date_id]:
                                message += f"\n\tالساعة: {time_name.strip()}"
                                self._available_dates[date_id].append(time_id)
            self.sendMessage(message) if message else None

    def run(self):
        api = Notification(governorates=self._required_governorates, logger=self._logger)
        countries = api.getCountries()
        while True:
            with ThreadPoolExecutor(28) as e:
                for country_name, country_id in countries.items():
                    # self.appointmentThread(country_name, country_id)
                    e.submit(self.appointmentThread, country_name, country_id)
            time.sleep(float(self._sleep))


if __name__ == "__main__":
    runner = Runner()
    runner.readSettings()
    runner.run()