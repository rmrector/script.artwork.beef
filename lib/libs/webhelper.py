import requests
from requests.adapters import HTTPAdapter
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

    def __call__(self, url, params=None, headers=None, timeout=20):
        # callers still need to handle Timeout, ConnectionError, HTTPError
        result = self.session.get(url, params=params, headers=headers, timeout=timeout)
        if result is None:
            return
        if result.status_code == 401:
            if self.login():
                result = self.session.get(url, params=params, headers=headers, timeout=timeout)
                if result is None:
                    return

        if result.status_code == 404:
            return
        result.raise_for_status()
        return result
