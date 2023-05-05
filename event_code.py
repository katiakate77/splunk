import logging
import os
import requests
import time
import urllib3

from dotenv import load_dotenv

from settings import MAX_EVENT_COUNT, SEARCH_QUERY_2

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
            event_counter = job_resp['entry'][0]['content']['eventCount']
            logging.info(
                f'Получили `isDone`: {is_done_check}, '
                f'`eventCount`: {event_counter}'
                )
        except KeyError:
            logging.error('Отсутствие `isDone` или `eventCount` в ответе API')
            raise KeyError('Нет ожидаемого ключа')
        return is_done_check, event_counter

    @classmethod
    def get_control_url(cls, sid):
        return cls.get_search_url() + '{}/control'.format(sid)

    def finalize_job(self, sid):
        job_control_url = self.get_control_url(sid)
        payload = {
            'action': 'finalize',
        }
        try:
            response = self.CURRENT_SESSION.post(
                job_control_url, data=payload
                )
            if response.ok:
                logging.info(f'Получили ответ от API {job_control_url}')
            else:
                logging.error(f'Не удалось получить ответ от API, '
                              f'код ошибки {response.status_code}')
                raise Exception(response.status_code)
        except Exception as e:
            logging.error(f'Недоступность эндпоинта, ошибка: {e}')
            raise Exception('Недоступность эндпоинта')

    def is_done(self, sid, max_event_count=MAX_EVENT_COUNT):
        done_check = False
        event_count = 0
        while not done_check:
            if event_count >= max_event_count:
                self.finalize_job(sid)
                logging.info('Останавливаем парсинг')
                logging.warning(
                    f'Найдено больше, чем {max_event_count} событий'
                    )
            time.sleep(2)
            resp_ = self.get_job_response(sid)
            done_check, event_count = self.parse_job_status(resp_)
        return True

    @classmethod
    def get_result_url(cls, sid):
        return cls.get_search_url() + '{}/results'.format(sid)

    def get_results(self, sid, offset=None, count=None):
        result_url = self.get_result_url(sid)
        if offset is None:
            offset = 0
        if count is None:
            count = 0
        params = {
            'offset': offset,
            'count': count,
        }
        payload = {
            'output_mode': 'json',
        }
        try:
            response = self.CURRENT_SESSION.get(
                result_url, params=params, data=payload
                )
            if response.ok:
                logging.info(f'Получили ответ от API {result_url}')
            else:
                logging.error(f'Не удалось получить ответ от API, '
                              f'код ошибки {response.status_code}')
                raise Exception(response.status_code)
        except Exception as e:
            logging.error(f'Недоступность эндпоинта, ошибка: {e}')
            raise Exception('Недоступность эндпоинта')
        return response.json()['results']


def get_result_filename():
    return f'RESULTS_{time.strftime("%d-%m-%y_%H:%M:%S")}.csv'


def main():
    job_1 = SplunkSearch()
    resp_1 = job_1.search_request(search_query=SEARCH_QUERY_2)
    sid_1 = job_1.parse_sid(resp_1)
    job_1.is_done(sid_1)
    offset_ = 0
    count_ = 5
    while True:
        res = job_1.get_results(sid_1, offset=offset_, count=count_)
        if res:
            print(res)
            logging.info('Печатаем результаты')
        else:
            break
        offset_ += count_
    print(get_result_filename())


if __name__ == '__main__':
    main()
