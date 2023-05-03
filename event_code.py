import logging
import os
import requests
# import time
import urllib3

from dotenv import load_dotenv

from settings import SEARCH_QUERY_1

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


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
        with requests.Session() as session:
            session.verify = False
            payload = {
                'username': cls.USERNAME,
                'password': cls.PASSWORD,
                'output_mode': 'json',
            }
            try:
                response = session.post(cls.get_auth_url(), data=payload)
                if response.ok:
                    logging.info(f'Получили ответ от API {cls.get_auth_url()}')
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

    # @classmethod
    # def set_headers(cls):
    #     session_, resp_ = cls.get_api_auth_answer()
    #     headers_ = cls.parse_session_key(resp_)
    #     session_.headers.update(headers_)
    #     logging.info('Установлены заголовки для всей сессии')
    #     return session_


class SplunkSearch(SplunkAuth):
    # CURRENT_SESSION = SplunkAuth.set_headers()
    @classmethod
    def set_headers(cls):
        session_, resp_ = cls.get_api_auth_answer()
        headers_ = cls.parse_session_key(resp_)
        session_.headers.update(headers_)
        logging.info('Установлены заголовки для всей сессии')
        return session_

    @classmethod
    def get_search_url(cls):
        app = 'search'
        return '{}{}/search/jobs/'.format(cls.get_base_url(), app)

    def search_request(self, search_query):
        payload = {
            'search': search_query,
            'output_mode': 'json',
        }
        try:
            response = self.set_headers().post(
                self.get_search_url(), data=payload
                )
            if response.ok:
                logging.info(f'Получили ответ от API {self.get_search_url()}')
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


# def get_job_status_url(sid):
#     return get_search_url() + '{}'.format(sid)


# def get_result_url(sid):
#     return get_search_url() + '{}/results'.format(sid)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        filename='log.log',
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    obj_1 = SplunkSearch()
    r_1 = obj_1.search_request(search_query=SEARCH_QUERY_1)
    obj_1.parse_sid(r_1)


if __name__ == '__main__':
    main()
