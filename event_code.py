import logging
import os
import requests
# import time
import urllib3

from dotenv import load_dotenv

from settings import SEARCH_QUERY_1

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


def get_api_auth_answer(sess):
    auth_url = get_auth_url()
    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'output_mode': 'json',
    }
    try:
        response = sess.post(auth_url, data=payload)
        if response.ok:
            logging.info(f'Получили ответ от API {auth_url}')
        else:
            logging.error(f'Не удалось получить ответ от API, '
                          f'код ошибки {response.status_code}')
            raise Exception(response.status_code)
    except Exception as e:
        logging.error(f'Недоступность эндпоинта, ошибка: {e}')
        raise Exception('Недоступность эндпоинта')
    return response.json()


def parse_session_key(response):
    try:
        sess_key = response.get('sessionKey')
        logging.info('Получили `sessionKey`')
    except KeyError:
        logging.error('Отсутствие `sessionKey` в ответе API')
        raise KeyError('Нет ожидаемого ключа')
    headers = {
        'Authorization': 'Splunk {}'.format(sess_key),
    }
    return headers


def get_search_url():
    app = 'search'
    return '{}{}/search/jobs/'.format(get_base_url(), app)


def search_request(sess, search_query):
    search_url = get_search_url()
    payload = {
        'search': search_query,
        'output_mode': 'json',
    }
    try:
        response = sess.post(search_url, data=payload)
        if response.ok:
            logging.info(f'Получили ответ от API {search_url}')
        else:
            logging.error(f'Не удалось получить ответ от API, '
                          f'код ошибки {response.status_code}')
            raise Exception(response.status_code)
    except Exception as e:
        logging.error(f'Недоступность эндпоинта, ошибка: {e}')
        raise Exception('Недоступность эндпоинта')
    return response.json()


def parse_sid(resp):
    try:
        sid = resp.get('sid')
        logging.info(f'Получили `sid`: {sid}')
    except KeyError:
        logging.error('Отсутствие `sid` в ответе API')
        raise KeyError('Нет ожидаемого ключа')
    return sid


def get_job_status_url(sid):
    return get_search_url() + '{}'.format(sid)


def get_result_url(sid):
    return get_search_url() + '{}/results'.format(sid)


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='log.log',
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    with requests.Session() as session:
        session.verify = False
        response = get_api_auth_answer(session)
        headers = parse_session_key(response)
        session.headers.update(headers)
        logging.info('Установлены заголовки для всей сессии')
        search_query_resp = search_request(session, SEARCH_QUERY_1)
        sid = parse_sid(search_query_resp)
        print(get_job_status_url(sid))


if __name__ == '__main__':
    main()
