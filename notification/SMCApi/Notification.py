from Core import ViewStateScrapper


class Notification(ViewStateScrapper):
    ENDPOINT = 'http://www.smcegy.com/karama/registerall.aspx'

    def __init__(self, **kwargs):
        super(Notification, self).__init__(**kwargs)
        self._governorates = {}
        self._required_governorates = kwargs.get('governorates', {'القاهره': 0, 'الاسكندريه': 0,
                                                                  'بورسعيد': 0, 'السويس': 0,
                                                                  'دمياط': 0, 'الدقهلية': 0,
                                                                  'الشرقية': 0, 'القليوبية': 0,
                                                                  'كفر الشيخ': 0, 'الغربية': 0,
                                                                  'المنوفية': 0, 'البحيرة': 0,
                                                                  'الاسماعيلية': 0, 'الجيزة': 0,
                                                                  'بني سويف': 0, 'الفيوم': 0,
                                                                  'المنيا': 0, 'أسيوط': 0,
                                                                  'سوهاج': 0, 'قنا': 0,
                                                                  'أسوان': 0, 'الاقصر': 0,
                                                                  'البحر الأحمر': 0, 'الوادى الجديد': 0,
                                                                  'مرسي مطروح': 0, 'شمال سيناء': 0,
                                                                  'جنوب سيناء': 0, 'اخرى': 0,
                                                                  'مولود خارج الجمهورية': 0})

    def getCountries(self):
        self._logger.debug("Trying to get countries")
        self._event_target = "ContentPlaceHolder1_txtCitizenSSN"
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel2|ContentPlaceHolder1_txtCitizenSSN',
            'txtCitizenSSN': '29811011701717',
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
            governorates = self.responseParsed.find('select', id="ContentPlaceHolder1_ddlGovernorate").find_all(
                'option')

            for governorate in governorates:
                if int(governorate.get('value')) and governorate.text.strip() in self._required_governorates:
                    self._governorates[governorate.text] = governorate.get('value')
            self._logger.debug("Countries Response Has Been Fetched")
        return self._governorates

    def getCity(self, governorate_id):
        self._logger.debug("Trying to get cities")
        districts_dict = {}
        self._event_target = 'ctl00$ContentPlaceHolder1$btnGetCity'
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$btnGetCity',
            'ddlGovernorate': governorate_id,
            'ddlCity': 0,
            'ddlCouncilId': 0
        }):
            districts = self.responseParsed.find('select', id='ContentPlaceHolder1_ddlCity').find_all('option')
            for district in districts:
                if int(district.get('value')) and district.text:
                    districts_dict[district.text] = district.get('value')
            self._logger.debug("cities Response Has Been Fetched")
        else:
            self._logger.log("Unable to fetch cities response", False)
        return districts_dict

    def getCouncil(self, governorate_id):
        self._logger.debug("Trying to get councils")
        councils_dict = {}
        self._event_target = 'ctl00$ContentPlaceHolder1$btnGetCity'
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$ddlCouncilId',
            'ddlGovernorate': governorate_id,
            'ddlCity': 0,
            'ddlCouncilId': 0
        }):
            councils = self.responseParsed.find('select', id='ContentPlaceHolder1_ddlCouncilId').find_all('option')
            for council in councils:
                if int(council.get('value')) and council.text:
                    councils_dict[council.text] = council.get('value')
            self._logger.debug("Councils Response Has Been Fetched")
        else:
            self._logger.log("Unable to fetch Councils response", False)
        return councils_dict

    def getAppointmentDate(self, governorate_id, council_id):
        self._logger.debug("Trying to get dates")
        appointment_days_dict = {}
        self._event_target = 'ctl00$ContentPlaceHolder1$ddlCouncilId'
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel3|ctl00$ContentPlaceHolder1$ddlCouncilId',
            'ddlGovernorate': governorate_id,
            'ddlCity': 0,
            'ddlCouncilId': council_id
        }):
            appointment_days = self.responseParsed.find('select', id='ContentPlaceHolder1_ddlComDate').find_all('option')
            for day in appointment_days:
                if int(day.get('value')) and day.text:
                    appointment_days_dict[day.text] = day.get('value')
            self._logger.debug("Dates Response Has Been Fetched")
        else:
            self._logger.log("Unable to fetch dates response", False)
        return appointment_days_dict

    def getAppointmentTime(self, governorate_id, council_id, date_id):
        self._logger.debug("Trying to get times")
        appointment_times_dict = {}
        self._event_target = 'ctl00$ContentPlaceHolder1$ddlComDate'
        if self.sendRequest('POST', self.ENDPOINT, data={
            'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel3|ctl00$ContentPlaceHolder1$ddlCouncilId',
            'ddlGovernorate': governorate_id,
            'ddlCity': 0,
            'ddlCouncilId': council_id,
            'ddlComDate': date_id
        }):
            appointment_time = self.responseParsed.find('select', id='ContentPlaceHolder1_ddlTimes').find_all('option')
            for time in appointment_time:
                if int(time.get('value')) and time.text:
                    appointment_times_dict[time.text] = time.get('value')
            self._logger.debug("Times Response Has Been Fetched")
        else:
            self._logger.log("Unable to fetch times response", False)
        return appointment_times_dict

    def governorates(self):
        return self._governorates


if __name__ == "__main__":
    notification_wrapper = Notification()
    # print(notification_wrapper.getCountries())
    # print(notification_wrapper.getCity(3))
    # print(notification_wrapper.getCouncil(3))
    # print(notification_wrapper.getAppointmentDate(3, 0))
    # print(notification_wrapper.getAppointmentTime(3, 0, 3))
    # print(notification_wrapper.getAppointmentTime(3, 0, 3))
    # print(notification_wrapper.getCity(1))
