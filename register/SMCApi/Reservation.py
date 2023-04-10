import time

from Core import ViewStateScrapper
import random


class Reservation(ViewStateScrapper):
    ENDPOINT = 'http://www.smcegy.com/karama/registerall.aspx'

    def __init__(self, **kwargs):
        super(Reservation, self).__init__(**kwargs)
        self._ssn = kwargs.get("ssn")
        self._first_name = kwargs.get("first_name")
        self._second_name = kwargs.get("second_name")
        self._third_name = kwargs.get("third_name")
        self._fourth_name = kwargs.get("fourth_name")
        self._city = kwargs.get("city")
        self._address = kwargs.get("address")
        self._phone_number = kwargs.get("phone_number")
        self._governorate = kwargs.get("governorate")
        self._martial_status = kwargs.get("martial_status")
        self._job = kwargs.get("job")
        self._ddl = kwargs.get("ddl")
        self._gender = 0
        self._council_id = 0
        self._date_id = 0
        self._time_id = 0
        self._date_name = ""
        self._time_name = ""
        self._council_name = ""
        self._request_id = ""
        self._ddl_inputs = {}
        self._dates = []
        self._times = []
        self._councils = []
        self.stage = 0
        self.done = False
        self.trials = 0
        self.start_time = 999999999999999999

    def submitSSN(self, close=False):
        self._logger.debug(f"Trying to submit {self._ssn}")
        self._event_target = "ContentPlaceHolder1_txtCitizenSSN"
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel2|ContentPlaceHolder1_txtCitizenSSN',
            'txtCitizenSSN': f'{self._ssn}',
            'txtFName': '',
            'txtSName': '',
            'txtTName': '',
            'txtLName': '',
            'txtBirthDate': '',
            'txtMonth': '',
            'txtAge': '',
            'ddlGender': '0',
            'txtAddress': '',
            'ddlMaritalStatus': '0',
            'ddlJob': '0',
            'txtPhone': '',
        }, close=close):
            gender_select = self._parsed_response.find("select", id="ContentPlaceHolder1_ddlGender")
            for gender in gender_select.find_all('option'):
                if gender.get("selected"):
                    self._gender = gender.get('value')
                    break
            self.stage += 1
            self.start_time = time.time()
            self._logger.debug(f"{self._ssn} submitted successfully")
            return True
        self.trials += 1
        self._logger.log(f"{self._ssn} couldn't be submitted")

    def submitGovernorate(self):
        self._logger.debug(f"Trying to submit governorate")
        self._event_target = "ctl00$ContentPlaceHolder1$btnGetCity"
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$btnGetCity',
            'txtFName': self._first_name,
            'txtSName': self._second_name,
            'txtTName': self._third_name,
            'txtLName': self._fourth_name,
            'ddlGender': self._gender,
            'ddlGovernorate': self._governorate,
            'ddlCity': '0',
            'ddlCouncilId': '0'
        }):
            for ddl in self._parsed_response.find_all('input', {'type': 'checkbox'}):
                if ddl.get("value") in self._ddl:
                    self._ddl_inputs[ddl.get("name")] = ddl.get("value")

            available_councils = self._parsed_response\
                .find('select', id='ContentPlaceHolder1_ddlCouncilId').find_all('option')
            for available_council in available_councils:
                if available_council.get('value') != "0":
                    self._councils.append((available_council.text, available_council.get('value')))
                    self._council_id = available_council.get('value')

            for city in self._parsed_response.find("select", id="ContentPlaceHolder1_ddlCity").find_all("option"):
                if city.text.strip() == self._city.strip():
                    self._city = city.get("value")
                    break
            self.stage += 1
            self._logger.debug(f"Governorate submitted successfully")
            return True
        self._logger.log(f"Governorate couldn't be submitted")

    def submitCouncil(self):
        self._logger.debug(f"Trying to submit council")
        self._event_target = "ctl00$ContentPlaceHolder1$ddlCouncilId"
        payload = {
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel3|ctl00$ContentPlaceHolder1$ddlCouncilId',
            'ddlCity': self._city,
            'txtAddress': self._address,
            'ddlMaritalStatus': self._martial_status,
            'ddlJob': self._job,
            'txtPhone': self._phone_number,
            'ddlCouncilId': self._council_id,
        }
        payload.update(self._ddl_inputs)
        if self.sendRequest('POST', self.ENDPOINT, data=payload):
            self._dates = []
            self._date_id = None
            self._date_name = ""
            for date in self._parsed_response.find('select', id="ContentPlaceHolder1_ddlComDate").find_all('option'):
                if date.get('value') != "0":
                    self._dates.append((date.text, date.get('value')))
            if not self._dates and self._councils:
                self._council_id = self._councils[-1][1]
                self._council_name = self._councils[-1][0]
                del self._councils[-1]
                return self.submitCouncil()
            elif not self._dates and not self._councils:
                self._logger.log(f"Council couldn't be submitted")
                return False
            else:
                self._date_name, self._date_id = random.choice(self._dates)
            self.stage += 1
            self._logger.debug(f"Council submitted successfully")
            return True
        self._logger.log(f"Council couldn't be submitted")

    def submitDate(self):
        self._logger.debug(f"Trying to submit Date")
        self._event_target = "ctl00$ContentPlaceHolder1$ddlComDate"
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel3|ctl00$ContentPlaceHolder1$ddlComDate',
            'ddlComDate': self._date_id,
        }):
            self._times = []
            self._time_id = None
            self._time_name = ""

            for time in self._parsed_response.find('select', id="ContentPlaceHolder1_ddlTimes").find_all('option'):
                if time.get('value') != "0":
                    self._times.append((time.text, time.get('value')))

            if not self._times and self._dates:
                self._date_id = self._dates[-1][1]
                self._date_name = self._dates[-1][0]
                del self._dates[-1]
                return self.submitDate()
            elif not self._times and not self._dates:
                self._logger.log(f"Date couldn't be submitted")
                return False
            else:
                self._time_name, self._time_id = random.choice(self._times)
            self.stage += 1
            self._logger.debug(f"Date submitted successfully")
            return True
        self._logger.log(f"Date couldn't be submitted")

    def submitTime(self):
        self._logger.debug(f"Trying to submit Time")
        self._event_target = ""
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel2|ctl00$ContentPlaceHolder1$btnSave',
            'ddlTimes': self._time_id,
            'btnSave': ' حفظ البيانات  '
        }):
            if not self._raw_response.startswith("1|#||4|42|pageRedirect||%2fKarama%2fViewAll.aspx%3freqId%3d"):
                return False
            self._request_id = self._raw_response.split("freqId%3d")[-1][:-1]
            self._logger.debug(f"Time submitted successfully")
            self.stage += 1
            self.done = True
            return True
        self._logger.log(f"Time couldn't be submitted")

    @property
    def request_url(self):
        return f"http://www.smcegy.com/Karama/ViewAll.aspx?reqId={self._request_id}"


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor

    def start():
        case_data = dict(
            ssn=random.randint(20012019998979, 20512012728979),
            first_name="askdjaksj",
            second_name="askljdaskl",
            third_name="asdjkaskld",
            fourth_name="asdqwjeqwk",
            address="askdjaskdqhejkqwhe jashdjksahd",
            martial_status="1",
            governorate="25",
            city="100",
            job="56",
            phone_number=f"01095978865",
            ddl=["1"],
        )
        reservation = Reservation(**case_data)
        reservation.submitSSN()
        reservation.submitGovernorate()
        reservation.submitCouncil()
        reservation.submitDate()
        for i in range(50):
            if reservation.submitTime():
                break
        reservation.submitTime()
        print(reservation.request_url)


    with ThreadPoolExecutor(5) as e:
        for i in range(100):
            e.submit(start)




