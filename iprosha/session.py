import logging
import requests

from .db import AuthDbAbstract

logging.basicConfig(level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logger = logging.getLogger()


class AuthSession:
    IPRO_URI = 'http://spb.etm.ru/ipro2'
    AUTH_URI = 'https://spb.etm.ru/ns2000/data-login.php'

    def __init__(self, login, auth_db: AuthDbAbstract):
        self._login = login
        self._man_id = None
        self._password = None
        self._login_type = 'WI'
        self._session_id = None

        self._session = requests.Session()
        self._db = auth_db
        self._is_login_data_in_db = False

        if self._db.is_exist_by_login(self._login):
            login_db_data = self._db.get_by_login(self._login)
            self._man_id = login_db_data.get('man_id')
            self._password = login_db_data.get('password')
            self._last_session_id = login_db_data.get('last_session_id')
            self._is_login_data_in_db = True

    def prepare_login_with_sms(self, password):
        self._password = password
        request_params = {
            't': 'login',
            'log': self._login,
            'pwd': self._password,
        }
        auth_json_response = self._session.get(self.AUTH_URI, params=request_params).json()
        if auth_json_response['msg'] == 'Неверный логин или пароль!':
            raise PermissionError('Error: Wrong login or password')

        self._session_id = auth_json_response.get('session')
        self._man_id = auth_json_response.get('man_id')
        self._login_type = auth_json_response.get('login_type')

        self.write_auth_data_to_db()
        logger.info('Sms auth prepared')

    def login_with_sms(self, sms_code):
        if not all([self._man_id, self._session_id]):
            raise AttributeError('Call prepare_login_with_sms before or initialize DB data to login:{}'.format(self._login))
        request_params = {'t': 'login',
                          'log': self._login,
                          'pwd': self._password,
                          'smsCode': sms_code,
                          'session': self._session_id, }
        logger.info('Fetching auth session for {}...'.format(self._login))
        self._session.get(self.AUTH_URI, params=request_params)
        logger.info('You authorized by sms. Session number is {}'.format(self._session_id))
        logger.info('Follow {} to seamless auth'.format(self.seamless_auth_link))

    def login_with_session_id(self, session_id):
        # Получить man-id получается только полностью авторизовавшись и сохранив его в БД
        if not self._is_login_data_in_db:
            raise AttributeError('You can not log in by session. You need the user {} store in the DB.'.format(self._login))
        self._session_id = session_id
        request_params = {'login': self._login,
                          'session': self._session_id,
                          'man-id': self._man_id,
                          'login_type': self._login_type, }
        resp = self._session.get(self.IPRO_URI, params=request_params)
        # Вход указывает что выбросило и нужно перезайти
        if 'Вход' in resp.text:
            raise Exception('You need to re-enter iPro')
        self.write_auth_data_to_db()
        logger.info('You authorized by session_id')
        logger.info('Follow {} to seamless auth'.format(self.seamless_auth_link))

    def write_auth_data_to_db(self):
        set_data = {'login': self._login,
                    'password': self._password,
                    'man_id': self._man_id,
                    'login_type': self._login_type,
                    'last_session_id': self._session_id, }
        self._db.set_by_login(self._login, **set_data)

    @property
    def seamless_auth_link(self):
        return '{url}/?login={login}&session={session_id}&man-id={man_id}&login_type={login_type}'.format(
            url=self.IPRO_URI,
            login=self._login,
            session_id=self._session_id,
            man_id=self._man_id,
            login_type=self._login_type,
        )

    @property
    def login(self):
        return self._login

    @property
    def password(self):
        return self._password

    @property
    def man_id(self):
        return self._man_id

    @property
    def login_type(self):
        return self._login_type

    @property
    def session_id(self):
        return self._session_id

    @property
    def session(self):
        return self._session
