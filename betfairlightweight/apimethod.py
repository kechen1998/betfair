import json
import datetime
from requests.exceptions import ConnectionError
from betfairlightweight.errors.apiexceptions import APIError, LogoutError, LoginError, KeepAliveError, BetfairError


class APIMethod:

    def __init__(self, api_client, method=None, params=None, exchange=None):
        self._api_client = api_client
        self.url = None
        self.payload = None
        self.method = method
        self.params = params
        self.exchange = exchange
        self.error = APIError
        self.instructions_length = 0

    @property
    def create_req(self):
        payload = {'jsonrpc': '2.0',
                   'method': self.method,
                   'params': self.params,
                   'id': 1}
        return json.dumps(payload)

    def create_resp(self, response, date_time_sent):
        if response.status_code == 200:
            return response.json(), response, date_time_sent
        else:
            raise self.error(response, self.params, self.method)

    def initiate_exchange(self, call_type):
        if not self.exchange:
            self.exchange = self._api_client.exchange
        if self.exchange == 'UK' or call_type in ['login', 'keep_alive', 'logout']:
            url = self._api_client.URL[call_type]
        elif self.exchange == 'AUS':
            url = self._api_client.URL_AUS[call_type]
        else:
            raise BetfairError
        return url

    def call(self, session=None):
        date_time_sent = datetime.datetime.now()
        if not session:
            session = self._api_client.request
        if self.method in ['SportsAPING/v1.0/placeOrders', 'SportsAPING/v1.0/replaceOrders']:
            self._api_client.check_transaction_count(self.instructions_length)
        try:
            response = session.post(self.url, data=self.create_req, headers=self._api_client.request_headers,
                                    timeout=(3.05, 12))
        except ConnectionError:
            raise APIError(None, self.params, self.method, 'ConnectionError')
        except Exception as e:
            raise APIError(None, self.params, self.method, e)
        return self.create_resp(response, date_time_sent)


class Login(APIMethod):

    def __init__(self, api_client):
        super(Login, self).__init__(api_client)
        self.url = self.initiate_exchange('login')
        self.error = LoginError

    def call(self, session=None):
        date_time_sent = datetime.datetime.now()
        if not session:
            session = self._api_client.request
        self.payload = 'username=' + self._api_client.username + '&password=' + self._api_client.password
        response = session.post(self.url, data=self.payload, headers=self._api_client.login_headers,
                                cert=self._api_client.cert)
        return self.create_resp(response, date_time_sent)


class KeepAlive(APIMethod):

    def __init__(self, api_client):
        super(KeepAlive, self).__init__(api_client)
        self.url = self.initiate_exchange('keep_alive')
        self.error = KeepAliveError

    def call(self, session=None):
        date_time_sent = datetime.datetime.now()
        if not session:
            session = self._api_client.request
        response = session.post(self.url, headers=self._api_client.keep_alive_headers, cert=self._api_client.cert)
        return self.create_resp(response, date_time_sent)


class Logout(APIMethod):

    def __init__(self, api_client):
        super(Logout, self).__init__(api_client)
        self.url = self.initiate_exchange('logout')
        self.error = LogoutError

    def call(self, session=None):
        date_time_sent = datetime.datetime.now()
        if not session:
            session = self._api_client.request
        response = session.get(self.url, headers=self._api_client.keep_alive_headers, cert=self._api_client.cert)
        return self.create_resp(response, date_time_sent)


class BettingRequest(APIMethod):

    def __init__(self, api_client, method, params, exchange):
        super(BettingRequest, self).__init__(api_client, method, params, exchange)
        if self.method in ['SportsAPING/v1.0/placeOrders', 'SportsAPING/v1.0/replaceOrders']:
            self.instructions_length = len(self.params['instructions'])
        self.url = self.initiate_exchange('betting')


class AccountRequest(APIMethod):

    def __init__(self, api_client, method, params, exchange):
        super(AccountRequest, self).__init__(api_client, method, params, exchange)
        self.url = self.initiate_exchange('account')


class ScoresRequest(APIMethod):

    def __init__(self, api_client, method, params):
        super(ScoresRequest, self).__init__(api_client, method, params)
        self.url = self.initiate_exchange('scores')


class NavigationRequest(APIMethod):

    def __init__(self, api_client, params):
        super(NavigationRequest, self).__init__(api_client, method=None, params=params)
        self._api_client = api_client
        self.params = params
        self.url = self.initiate_exchange('NAVIGATION')

    def call(self, session=None):
        date_time_sent = datetime.datetime.now()
        headers = self._api_client.request_headers
        try:
            response = self._api_client.request.get(self.url, headers=headers, timeout=(3.05, 12))
        except Exception as e:
            raise APIError(None, self.params, e)
        return self.create_resp(response, date_time_sent)
