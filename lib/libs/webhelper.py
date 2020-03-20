import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, Timeout, RequestException
# import from `requests` because Jarvis / some platforms still have old urllib3
from requests.packages.urllib3.util.retry import Retry

def retryable_session(retries=3, backoff_factor=0.5, status_forcelist=(500, 502, 504, 520), session=None):
    # from https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    session = session or requests.Session()
    # 'Retry-After' 413/503/529 headers are respected by default
    retry = Retry(total=retries, read=retries, connect=retries,
        backoff_factor=backoff_factor, status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class Getter(object):
    def __init__(self, contenttype=None, login=lambda: False, session=None):
        self.session = session or retryable_session()
        self.login = login
        if contenttype:
            self.session.headers['Accept'] = contenttype

    def __call__(self, url, **kwargs):
        try:
            return self._inner_call(url, **kwargs)
        except (Timeout, ConnectionError, RequestException) as ex:
            message = ex.response.reason if getattr(ex, 'response', None) is not None else type(ex).__name__
            raise GetterError(message, ex, not isinstance(ex, RequestException))

    def _inner_call(self, url, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 20
        result = self.session.get(url, **kwargs)
        if result is None:
            return
        if result.status_code == 401:
            if self.login():
                result = self.session.get(url, **kwargs)
                if result is None:
                    return

        if result.status_code == 404:
            return
        result.raise_for_status()
        return result

class GetterError(Exception):
    def __init__(self, message, cause, connection_error):
        super(GetterError, self).__init__()
        self.message = message
        self.cause = cause
        self.connection_error = connection_error
        self.request = getattr(cause, 'request', None)
        self.response = getattr(cause, 'response', None)
