import re
from httpx import Client
from requests import Session
from Core import Logger
from bs4 import BeautifulSoup
from warnings import simplefilter
from random_user_agent.user_agent import UserAgent
from collections import OrderedDict
simplefilter('ignore')


class ViewStateScrapper:
    BASE_URL = 'http://www.smcegy.com/karama/Grievance.aspx'
    def __init__(self, **kwargs):
        self._logger = kwargs.get('logger', Logger(debug=True))

        self._useragent = kwargs.get('useragent', UserAgent().get_random_user_agent())

        self._host = kwargs.get("host", "www.smcegy.com")
        self._origin = kwargs.get("origin", f'http://www.smcegy.com')
        self._referer = kwargs.get('referer', f'http://www.smcegy.com/')
        self._form_id = kwargs.get("form_id", "form1")

        self._session = Session()
        self._parsed_response = ""
        self._raw_response = ""

        self._event_target = kwargs.get('_event_target', "")
        self._view_state = kwargs.get('_view_state', "")
        self._view_state_generator = kwargs.get('_view_state_generator', "115C55A6")
        self._event_validation = kwargs.get('_event_validation', "")
        self._async_post = "true"

        self._form_prefix = kwargs.get('form_prefix', 'ctl00$ContentPlaceHolder1$')
        self._inputs = kwargs.get('input', {})
        self._initRequest()
        self._initSessionHeaders()


    def _initSessionHeaders(self):
        self._referer = self.BASE_URL
        self._session.headers.update({
            'connection': None,
            'accept-encoding': None,
            'accept': '*/*',
            'accept-language': "en-US,en;q=0.9",
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'host': self._host,
            'origin': self._origin,
            'referer': self._referer,
            'user-agent': self._useragent,
            'x-microsoftajax': "Delta=true",
            'x-requested-with': "XMLHttpRequest"
        })

    def _initRequest(self):
        try:
            self._logger.debug(f"Trying to init view state request, {self._referer}")
            init_response = self._session.get(self.BASE_URL, headers={
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': "en-US,en;q=0.9",
                'host': self._host,
                'referer': self._referer,
                'upgrade-insecure-requests': '1',
                'user-agent': self._useragent,
            })
            parsed = BeautifulSoup(init_response.text)
            form = parsed.find('form', id=self._form_id)
            self._parsed_response = form
            self._view_state = form.find('input', id='__VIEWSTATE')['value']
            self._event_validation = form.find('input', id='__EVENTVALIDATION')['value']
            self._logger.debug("View State has been fetched successfully")
            return True
        except Exception as e:
                self._logger.log(f"An error occurred while trying to init request.\n\t errors: {e}", True)
        return False

    def _initRequestData(self, inputs):
        data = OrderedDict(**{
            f'{self._form_prefix}ScriptManager1': None,
            f'{self._form_prefix}txtCitizenSSN': None,
            f'{self._form_prefix}txtFName': None,
            f'{self._form_prefix}txtSName': None,
            f'{self._form_prefix}txtTName': None,
            f'{self._form_prefix}txtLName': None,
            f'{self._form_prefix}txtBirthDate':None,
            f'{self._form_prefix}txtMonth': None,
            f'{self._form_prefix}txtAge': None,
            f'{self._form_prefix}ddlGender': None,
            f'{self._form_prefix}ddlGovernorate': None,
            f'{self._form_prefix}ddlCity': None,
            f'{self._form_prefix}txtAddress': None,
            f'{self._form_prefix}ddlMaritalStatus': None,
            f'{self._form_prefix}ddlJob': None,
            f'{self._form_prefix}txtPhone': None,
            f'{self._form_prefix}chbDistype$0': None,
            f'{self._form_prefix}chbDistype$1': None,
            f'{self._form_prefix}chbDistype$2': None,
            f'{self._form_prefix}chbDistype$3': None,
            f'{self._form_prefix}chbDistype$4': None,
            f'{self._form_prefix}ddlCouncilI5': None,
            f'{self._form_prefix}ddlComDate': None,
            f'{self._form_prefix}ddlTimes': None,
            '__EVENTTARGET': self._event_target,
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': self._view_state,
            '__VIEWSTATEGENERATOR': self._view_state_generator,
            '__EVENTVALIDATION': self._event_validation,
            '__ASYNCPOST': 'true',
            f'{self._form_prefix}btnSave': None,
        })

        if inputs:
            for key, value in inputs.items():
                if str(key).startswith('__'):
                    continue
                if value is None:
                    continue
                self._inputs[f"{self._form_prefix}{str(key).replace(self._form_prefix, '')}"] = str(value)
                data.update(self._inputs)
        return data

    def _parseResponseData(self, response):
        if response.status_code == 200 and response.text.startswith('1|#||4|'):
            html_response = re.findall('<(.*)>', response.text, re.MULTILINE | re.DOTALL)
            html_response_parsed = BeautifulSoup(html_response[0])
            self._parsed_response = html_response_parsed
            for input_ in html_response_parsed.find_all('input'):
                if input_['name'] not in self._inputs:
                    continue
                self._inputs[input_['name']] = input_.get('value', '')

            self._view_state = \
            re.findall(r'\|[0-9]*\|hiddenField\|__VIEWSTATE\|(.*?)\|',
                       response.text, re.MULTILINE | re.DOTALL)[0]
            self._event_validation = \
            re.findall(r'\|[0-9]*\|hiddenField\|__EVENTVALIDATION\|(.*?)\|',
                       response.text, re.MULTILINE | re.DOTALL)[0]
            return True
        self._logger.log("An error occurred while trying to parsed response data", True)
        return response.text.startswith('1|#||4|')

    def sendRequest(self, method, url, **kwargs):
        try:
            close = kwargs.pop('close') if 'close' in kwargs else False
            kwargs.update({'data': self._initRequestData(kwargs.get('data'))})
            response = self._session.request(method, url, **kwargs)
            if close:
                response.close()
                return

            print("".center(50, '-'))
            self._logger.debug("Headers".center(50))
            for header_name, header_value in response.request.headers.items():
                self._logger.debug(f"{header_name}: {header_value}")

            print("Body".center(50))
            for key, value in (kwargs.get('data', {}) or {}).items():
                print(f"{key}: {str(value)}") if key not in ['__VIEWSTATE', '__EVENTVALIDATION'] else None
            print("".center(50, '-'))

            print(response.text[0:100])

            # with open('response.html', 'w+') as response_writer:
            #     response_writer.write(response.request)

            self._raw_response = response.text
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
        self._event_target = ""
        self._view_state = ""
        self._view_state_generator = ""
        self._event_validation = ""

        return {
            '_last_focus': '',
            '_event_target': self._event_target,
            '_event_argument': '',
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
