from Core import ViewStateScrapper
import time
import random


class Grievance(ViewStateScrapper):
    ENDPOINT = 'http://www.smcegy.com/karama/Grievance.aspx'

    def __init__(self, **kwargs):
        super(Grievance, self).__init__(referer="http://www.smcegy.com/karama/Grievance.aspx",
                                        **kwargs)
        self._ssn = kwargs.get("ssn")
        self._ddl = kwargs.get("ddl")
        self._gender = 0
        self._council_id = 0
        self._date_id = 0
        self._time_id = 0
        self._council_name = kwargs.get("council_name")
        self._date_name = ""
        self._time_name = ""
        self._request_id = ""
        self._ddl_inputs = {}
        self._dates = []
        self._times = []
        self._councils = []
        self.stage = 0
        self.done = False
        self.start_time = 999999999999999999

    def submitSSN(self):
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
            'txtPhone': ''
        }):
            gender_select = self._parsed_response.find("select", id="ContentPlaceHolder1_ddlGender")
            for gender in gender_select.find_all('option'):
                if gender.get("selected"):
                    self._inputs['ctl00$ContentPlaceHolder1$ddlGender'] = gender.get("value")
                    break

            martial_status_select= self._parsed_response.find('select', id="ContentPlaceHolder1_ddlMaritalStatus")
            for status in martial_status_select.find_all('option'):
                if status.get('selected'):
                    self._inputs['ctl00$ContentPlaceHolder1$ddlMaritalStatus'] = status.get("value")

            jobs_select= self._parsed_response.find('select', id="ContentPlaceHolder1_ddlJob")
            for job in jobs_select.find_all('option'):
                if job.get('selected'):
                    self._inputs['ctl00$ContentPlaceHolder1$ddlJob'] = job.get("value")

            governorate_select = self._parsed_response.find("select", id="ContentPlaceHolder1_ddlGovernorate")
            for governorate in governorate_select.find_all("option"):
                if governorate.get("selected"):
                    self._inputs['ctl00$ContentPlaceHolder1$ddlGovernorate'] = governorate.get("value")
                    break

            city_select = self._parsed_response.find("select", id="ContentPlaceHolder1_ddlCity")
            for city in city_select.find_all("option"):
                if city.get("selected"):
                    self._inputs['ctl00$ContentPlaceHolder1$ddlCity'] = city.get("value")
                    break

            for council in self._parsed_response.find("select", id="ContentPlaceHolder1_ddlCouncilId").find_all("option"):
                if council.text == self._council_name:
                    self._council_id = council.get("value")
                    break

            for ddl in self._parsed_response.find_all('input', {'type': 'checkbox'}):
                if ddl.get("value") in self._ddl:
                    self._ddl_inputs[ddl.get("name")] = ddl.get("value")

            self.stage += 1
            self.start_time = time.time()
            self._logger.debug(f"{self._ssn} submitted successfully")
            return True
        self._logger.log(f"{self._ssn} couldn't be submitted")

    def submitCouncil(self):
        self._logger.debug(f"Trying to submit council")
        self._event_target = "ctl00$ContentPlaceHolder1$ddlCouncilId"
        payload = {
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel3|ctl00$ContentPlaceHolder1$ddlCouncilId',
            'ddlCouncilId': self._council_id,
        }
        payload.update(self._ddl_inputs)
        if self.sendRequest('POST', self.ENDPOINT, data=payload):
            for date in self._parsed_response.find('select', id="ContentPlaceHolder1_ddlComDate").find_all('option'):
                if date.get('value') != "0":
                    self._date_id = date.get('value')
                    self._date_name = date.text
                    break
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
        if not self._time_id:
            return False
        self._event_target = ""
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel2|ctl00$ContentPlaceHolder1$btnSave',
            'ddlTimes': self._time_id,
            'btnSave': ' حفظ طلب التظلم  '
        }):
            if not self._raw_response.startswith("1|#||4|42|pageRedirect||%2fKarama%2fViewAll.aspx%3freqId%3d"):
                return False
            self._request_id = self._raw_response.split("freqId%3d")[-1][:-1]
            self.done = True
            self.stage += 1
            self._logger.debug(f"Time submitted successfully")
            return True
        self._logger.log(f"Time couldn't be submitted")

    @property
    def request_url(self):
        return f"http://www.smcegy.com/Karama/ViewAll.aspx?reqId={self._request_id}"



if __name__ == "__main__":
    reservation = Grievance(ssn="26110281300839", ddl=[
        'إعاقة حركية'
    ])
    reservation.submitSSN()
    reservation.submitCouncil()
    reservation.submitDate()
    reservation.submitTime()
    print(reservation.request_url)