import re

from requests import Session
from Core import Logger
from bs4 import BeautifulSoup
from warnings import simplefilter

simplefilter('ignore')


class ViewStateScrapper:
    def __init__(self, **kwargs):
        self._logger = kwargs.get('logger', Logger())

        self._useragent = kwargs.get('user-agent',
                                     'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                                     ' Chrome/106.0.0.0 Safari/537.36')

        self._host = kwargs.get("host", "www.smcegy.com")
        self._origin = kwargs.get("origin", f'http://{self._host}')
        self._referer = kwargs.get('referer', f'http://{self._host}/karama/registerall.aspx')
        self._form_id = kwargs.get("form_id", "form1")

        self._session = Session()
        self._parsed_response = ""
        self._raw_response = ""

        self._last_focus = kwargs.get('_last_focus', "")
        self._event_target = kwargs.get('_event_target', "")
        self._event_argument = kwargs.get('_event_argument', "")
        self._view_state = kwargs.get('_view_state', "")
        self._view_state_generator = kwargs.get('_view_state_generator', "")
        self._view_state_encrypted = kwargs.get("_view_state_encrypted", "")
        self._event_validation = kwargs.get('_event_validation', "")
        self._async_post = "true"

        self._form_prefix = kwargs.get('form_prefix', 'ctl00$ContentPlaceHolder1$')
        self._inputs = kwargs.get('input', {})

        self._initSessionHeaders()
        self._initRequest()

    def _initSessionHeaders(self):
        self._session.headers.update({
            'Accept': '*/*',
            'Accept-Language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'DNT': "1",
            'Host': self._host,
            'Origin': self._origin,
            'Pragma': "no-cache",
            'Referer': self._referer,
            'User-Agent': self._useragent,
            'X-MicrosoftAjax': "Delta=true",
            'X-Requested-With': "XMLHttpRequest"
        })

    def _initRequest(self):
        try:
            self._logger.debug(f"Trying to init view state request, {self._referer}")
            with self._session.get(self._referer) as init_response:
                parsed = BeautifulSoup(init_response.text)
                form = parsed.find('form', id=self._form_id)
                self._parsed_response = form
                self._view_state = form.find('input', id='__VIEWSTATE')['value']
                self._view_state_generator = form.find('input', id="__VIEWSTATEGENERATOR")['value']
                self._event_validation = form.find('input', id='__EVENTVALIDATION')['value']
                self._last_focus = form.find('input', id='__LASTFOCUS')['value']
                self._event_argument = form.find('input', id='__EVENTARGUMENT')['value']
                self._event_target = form.find('input', id='__EVENTTARGET')['value']
                self._view_state_encrypted = form.find('input', id="__VIEWSTATEENCRYPTED")
                self._view_state_encrypted = self._view_state_encrypted['value'] if self._view_state_encrypted else None
                self._logger.debug("View State has been fetched successfully")
                return True
        except Exception as e:
            self._logger.log(f"An error occurred while trying to init request.\n\t errors: {e}", True)
        return False

    def _initRequestData(self, inputs):
        self._logger.debug("Trying to init request data")
        data = {}
        if inputs:
            data.update({'__VIEWSTATE': self._view_state,
                         '__VIEWSTATEGENERATOR': self._view_state_generator,
                         '__EVENTVALIDATION': self._event_validation,
                         '__LASTFOCUS': self._last_focus,
                         '__EVENTARGUMENT': self._event_argument,
                         '__EVENTTARGET': self._event_target})

            for key, value in inputs.items():
                if str(key).startswith('__'):
                    continue
                self._inputs[f"{self._form_prefix}{str(key).replace(self._form_prefix, '')}"] = str(value)
                data.update(self._inputs)
        return data

    def _parseResponseData(self, response):
        self._logger.debug("Trying to parse response")
        if response.status_code == 200 and response.text.startswith('1|#||4|'):
            html_response = re.findall('<(.*)>', response.text, re.MULTILINE | re.DOTALL)
            html_response_parsed = BeautifulSoup(html_response[0])
            self._parsed_response = html_response_parsed
            for input_ in html_response_parsed.find_all('input'):
                if input_['name'] not in self._inputs:
                    continue
                self._inputs[input_['name']] = input_.get('value', '')
            self._last_focus = \
            re.findall(r'\|0\|hiddenField\|__LASTFOCUS\|(.*?)\|', response.text, re.MULTILINE | re.DOTALL)[0]
            self._event_target = \
            re.findall(r'\|0\|hiddenField\|__EVENTTARGET\|(.*?)\|', response.text, re.MULTILINE | re.DOTALL)[0]
            self._event_argument = \
            re.findall(r'\|0\|hiddenField\|__EVENTARGUMENT\|(.*?)\|', response.text, re.MULTILINE | re.DOTALL)[0]
            self._view_state = \
            re.findall(r'\|[0-9]*\|hiddenField\|__VIEWSTATE\|(.*?)\|', response.text, re.MULTILINE | re.DOTALL)[0]
            self._view_state_generator = \
            re.findall(r'\|[0-9]*\|hiddenField\|__VIEWSTATEGENERATOR\|(.*?)\|', response.text,
                       re.MULTILINE | re.DOTALL)[0]
            self._event_validation = \
            re.findall(r'\|[0-9]*\|hiddenField\|__EVENTVALIDATION\|(.*?)\|', response.text, re.MULTILINE | re.DOTALL)[0]
            self._logger.debug("Response data has been parsed successfully")
            return True
        self._logger.log("An error occurred while trying to parsed response data", True)
        return response.text.startswith('1|#||4|')

    def sendRequest(self, method, url, **kwargs):
        try:
            kwargs.update({'data': self._initRequestData(kwargs.get('data'))})
            self._logger.debug('Trying to send request')
            response = self._session.request(method, url, **kwargs)
            self._raw_response = response.text
            self._logger.debug('Request has been sent successfully')
            return self._parseResponseData(response)
        except Exception as e:
            self._logger.log(f'An error occurred while trying to send request.\n\t errors: {e}', True)
        return self._raw_response.startswith('1|#||4|')

    @property
    def inputs(self):
        return self._inputs

    @property
    def responseParsed(self):
        return self._parsed_response

    @property
    def getStateInfo(self):
        self._last_focus = ""
        self._event_target = ""
        self._event_argument = ""
        self._view_state = ""
        self._view_state_generator = ""
        self._event_validation = ""

        return {
            '_last_focus': self._last_focus,
            '_event_target': self._event_target,
            '_event_argument': self._event_argument,
            '_view_state': self._view_state,
            '_view_state_generator': self._view_state_generator,
            '_event_validation': self._event_validation
        }


if __name__ == "__main__":
    scrapper = ViewStateScrapper()
    scrapper.sendRequest('POST', 'http://www.smcegy.com/karama/registerall.aspx', data={
        'ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel2|ContentPlaceHolder1_txtCitizenSSN',
        'txtCitizenSSN': '29811011701717',
        'txtFName': 'islam',
        'txtSName': 'elsayed',
        'txtTName': 'bassiouny',
        'txtLName': 'ali',
        'txtBirthDate': '',
        'txtMonth': '',
        'txtAge': '',
        'ddlGender': 1,
        'txtAddress': 'fake address',
        'ddlMaritalStatus': 1,
        'ddlJob': 33,
        'txtPhone': '01094950765'
    })
