# import logging
import os
import requests
import urllib3

from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

SCHEME = os.getenv('SCHEME')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')


def get_base_url():
    return '{}://{}:{}/servicesNS/{}/'.format(SCHEME, HOST, PORT, USERNAME)


def get_auth_url():
    app = 'system'
    return '{}{}/auth/login/'.format(get_base_url(), app)


def get_api_auth_answer():
    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'output_mode': 'json',
    }
    try:
        response = requests.post(get_auth_url(), data=payload, verify=False)
        if not response.ok:
            raise Exception(response.status_code)
    except Exception:
        raise Exception('Недоступность эндпоинта')
    return response.json()


def parse_session_key():
    try:
        sess_key = get_api_auth_answer().get('sessionKey')
    except KeyError:
        raise KeyError('Нет ожидаемого ключа')
    headers = {
        'Authorization': 'Splunk {}'.format(sess_key),
    }
    return headers


print(get_base_url())
print(get_auth_url())
print(get_api_auth_answer())
print(parse_session_key())
