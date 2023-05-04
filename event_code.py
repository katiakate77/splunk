import logging
import os
import requests
import time
import urllib3

from dotenv import load_dotenv

from settings import SEARCH_QUERY_1

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='log.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
)


class SplunkBase:
    SCHEME = os.getenv('SCHEME')
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')

    @classmethod
    def get_base_url(cls):
        return '{}://{}:{}/servicesNS/{}/'.format(
            cls.SCHEME, cls.HOST, cls.PORT, cls.USERNAME
            )


class SplunkAuth(SplunkBase):
    @classmethod
    def get_auth_url(cls):
        app = 'system'
        return '{}{}/auth/login/'.format(cls.get_base_url(), app)

    @classmethod
    def get_api_auth_answer(cls):
        auth_url = cls.get_auth_url()
        with requests.Session() as session:
            session.verify = False
            payload = {
                'username': cls.USERNAME,
                'password': cls.PASSWORD,
                'output_mode': 'json',
            }
            try:
                response = session.post(auth_url, data=payload)
                if response.ok:
                    logging.info(f'Получили ответ от API {auth_url}')
                else:
                    logging.error(f'Не удалось получить ответ от API, '
                                  f'код ошибки {response.status_code}')
                    raise Exception(response.status_code)
            except Exception as e:
                logging.error(f'Недоступность эндпоинта, ошибка: {e}')
                raise Exception('Недоступность эндпоинта')
            return session, response.json()

    @classmethod
    def parse_session_key(cls, resp):
        try:
            sess_key = resp.get('sessionKey')
            logging.info('Получили `sessionKey`')
        except KeyError:
            logging.error('Отсутствие `sessionKey` в ответе API')
            raise KeyError('Нет ожидаемого ключа')
        headers = {
            'Authorization': 'Splunk {}'.format(sess_key),
        }
        return headers

    @classmethod
    def set_headers(cls):
        session_, resp_ = cls.get_api_auth_answer()
        headers_ = cls.parse_session_key(resp_)
        session_.headers.update(headers_)
        logging.info('Установлены заголовки для всей сессии')
        return session_


class SplunkSearch(SplunkAuth):
    CURRENT_SESSION = SplunkAuth.set_headers()

    @classmethod
    def get_search_url(cls):
        app = 'search'
        return '{}{}/search/jobs/'.format(cls.get_base_url(), app)

    def search_request(self, search_query):
        search_url = self.get_search_url()
        payload = {
            'search': search_query,
            'output_mode': 'json',
        }
        try:
            response = self.CURRENT_SESSION.post(
                search_url, data=payload
                )
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

    def parse_sid(self, resp):
        try:
            sid = resp.get('sid')
            logging.info(f'Получили `sid`: {sid}')
        except KeyError:
            logging.error('Отсутствие `sid` в ответе API')
            raise KeyError('Нет ожидаемого ключа')
        return sid

    @classmethod
    def get_job_status_url(cls, sid):
        return cls.get_search_url() + '{}'.format(sid)

    def get_job_response(self, sid):
        job_status_url = self.get_job_status_url(sid)
        payload = {
            'output_mode': 'json',
        }
        try:
            response = self.CURRENT_SESSION.get(
                job_status_url, data=payload
                )
            if response.ok:
                logging.info(f'Получили ответ от API {job_status_url}')
            else:
                logging.error(f'Не удалось получить ответ от API, '
                              f'код ошибки {response.status_code}')
                raise Exception(response.status_code)
        except Exception as e:
            logging.error(f'Недоступность эндпоинта, ошибка: {e}')
            raise Exception('Недоступность эндпоинта')
        return response.json()

    def parse_job_status(self, job_resp):
        try:
            is_done_check = job_resp['entry'][0]['content']['isDone']
            logging.info(f'Получили `isDone`: {is_done_check}')
        except KeyError:
            logging.error('Отсутствие `isDone` в ответе API')
            raise KeyError('Нет ожидаемого ключа')
        return is_done_check

    def is_done(self, sid):
        done_check = False
        while not done_check:
            time.sleep(2)
            resp_ = self.get_job_response(sid)
            done_check = self.parse_job_status(resp_)
        return True

    @classmethod
    def get_result_url(cls, sid):
        return cls.get_search_url() + '{}/results'.format(sid)


def main():
    job_1 = SplunkSearch()
    resp_1 = job_1.search_request(search_query=SEARCH_QUERY_1)
    sid_1 = job_1.parse_sid(resp_1)
    resp_2 = job_1.is_done(sid_1)
    print(resp_2)


if __name__ == '__main__':
    main()
