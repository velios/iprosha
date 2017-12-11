import re
import json
from collections import namedtuple

import pendulum

from .session import AuthSession
from .utils import clean_html_tags


class IProBaseClient:
    def __init__(self, session: AuthSession):
        self._session = session.session
        self._auth_data = session

    @property
    def full_client_list(self):
        CLIENT_INFO_URI = 'http://spb.etm.ru/cat/man-info.html'
        CLIENT_INFO_JSON_URI = 'http://spb.etm.ru/cat/data-orgtree.html'
        ClientInfo = namedtuple('ClientInfo', ['id', 'name', 'specialization', 'worth', 'warm'])

        client_info_raw_html = self._session.get(CLIENT_INFO_URI)
        client_info_raw_html.encoding = 'cp1251'
        client_info_id = re.search('{"ID":"(\d+)",', client_info_raw_html.text).group(1)
        request_params = {'id': client_info_id}
        client_info_raw_json = self._session.get(CLIENT_INFO_JSON_URI, params=request_params)
        client_info_json = json.loads(client_info_raw_json.text)['Nodes']

        client_info_list = []
        for client_info in client_info_json:
            client_id = client_info['ID']
            name, specialization, worth, warm = re.match(r'(.+) \((\S+),~(\S+), +(.+)\)', client_info['Name']).groups()
            client_info_list.append(ClientInfo(
                id=client_id,
                name=clean_html_tags(name),
                specialization=specialization,
                worth=worth,
                warm=warm
            ))
        return client_info_list

    def setup_plan_to_company(self, client_id, to_for_month, rtn_for_month, month=None, year=None):
        PLAN_URI = 'http://spb.etm.ru/cat/data-plan.html'
        now = pendulum.now('Europe/Moscow')
        year = year if year else now.year
        month = month if month else now.month

        plan_params = {
            'id': client_id,
            'login': self._auth_data._login,
            'man': self._auth_data._man_id,
            'usr': self._auth_data._man_id,
            'month': month,
            'year': year,
            'to': int(to_for_month),
            'rtn': float(rtn_for_month),
            'cause': 'завершение объекта',
        }
        self._session.post(PLAN_URI, params=plan_params)

    def fill_schedule_task(self, client_id, task_date, task_message, task_result=None):  # $("#dialog_delete").dialog("open");
        client_schedule_post_url = 'http://ipro.etm.ru/cat/runprog.html'
        schedule_request_params = {
            'man': self._auth_data._man_id,
            'login': self._auth_data._login,
            # TODO: Разобраться с номером офиса
            'pme_persons': 'pmp_class37^{office}$man-code^{man_id}$cli-code^{client_code}$exm_mancode^'.format(man_id=self._auth_data._man_id,
                                                                                                               client_code=client_id,
                                                                                                               office='ССПб3'),
            'pme_datep': task_date,
            'pme_task': task_message,
            'pme_result': task_result,
            # TODO: Почистить параметры под todo проверив их в curl
            'syf_prog': 'pr_meeting-rsp',
            'withoutArchive': 'yes',
            'RSPAction': 'A',
            'pme_state': 'appoint',
            'RO_theme': 'Развитие продаж',
            'pme_theme': 'ВТ10',
            'RO_subtheme': 'Встречи с партнёрами',
            'pme_subtheme': 'ВТ1010',
            'RO_type': 'Встреча с партнёром',
            'pme_type': 'ВМ10',
        }
        self._session.get(client_schedule_post_url, params=schedule_request_params)
