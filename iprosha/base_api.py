import re
import json
from collections import namedtuple

import pendulum
from bs4 import BeautifulSoup

from .session import AuthSession, logger
from .utils import clean_html_tags



class IProBaseClient:
    def __init__(self, session: AuthSession):
        self._session = session.session
        self._auth_data = session

    @property
    def client_info_list(self):
        CLIENT_INFO_URI = 'http://spb.etm.ru/cat/man-info.html'
        CLIENT_INFO_JSON_URI = 'http://spb.etm.ru/cat/data-orgtree.html'
        ClientInfo = namedtuple('ClientInfo', ['id', 'name', 'specialization', 'worth', 'warm'])

        client_info_raw_html = self._session.get(CLIENT_INFO_URI)
        client_info_raw_html.encoding = 'cp1251'
        client_info_id = re.search(r'{"ID":"(\d+)",', client_info_raw_html.text).group(1)
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

    @property
    def manager_info_dict(self):
        MANAGER_PROFILE_URI = 'http://spb.etm.ru/cat/man-profile.html'
        html_doc = self._session.get(MANAGER_PROFILE_URI)
        html_doc.encoding = 'cp1251'
        soup = BeautifulSoup(html_doc.text, 'html.parser')

        info_table_body = soup.find_all('tr')
        fio = soup.find(id='fio').text
        try:
            position, position_code = re.match(r'Должность:(.+)\s+\((.+)\)', info_table_body[2].text).groups()
        except:
            position, position_code = None, None

        return {
            'fio': fio,
            'admin': soup.find(id='admin').get('value'),
            'ktu': soup.find(id='ktu').get('value'),
            'phone': soup.find(id='phone').get('value'),
            'e_mail': soup.find(id='e-mail').get('value'),
            'prefix': soup.find(id='prefix').get('value'),
            # Хз что такое "текущий номер"
            'current_number': soup.find(id='number').get('value'),
            'sms_phone': soup.find(id='phoneID').get('value'),
            'enter_login': soup.find(id='userAD').get('value'),
            'ip_phone': soup.find(id='phoneIP').get('value'),
            'city_phone': soup.find(id='phoneCity').get('value'),
            'city_phone_dob': soup.find(id='phoneCityD').get('value'),
            'skype': soup.find(id='skype').get('value'),
            'position': position,
            'position_code': position_code,
        }

    def fetch_user_tasks(self,
                         status_filter=None,
                         start_date=pendulum.now('Europe/Moscow').start_of('month').format('D/M/YY', formatter='alternative'),
                         end_date=pendulum.now('Europe/Moscow').end_of('month').format('D/M/YY', formatter='alternative')):
        # Формат start_date и end_date - Pendulum Date Format
        TaskInfo = namedtuple('TaskInfo', ['id', 'subtheme', 'plan_date', 'fact_date', 'type', 'client', 'manager', 'task', 'status', 'documents', 'result', 'pme_subtheme'])
        CALENDAR_URI = 'http://ipro.etm.ru/cat/buildbrowser.html'
        calendar_params = {
            'man': self._auth_data._man_id,
            'login': self._auth_data._login,
            'syf_prog': 'pr_meeting-rsp',
            'RSPAction': 'B',
            'body': 'pr_meeting',
            'whichTableRowid': 'pr_meeting',
            # Назначено
            # 'filterpme_state': 'appoint',
            'fieldlist': 'RO_subtheme,pme_datep,pme_datef,RO_type,RO_client^all,RO_person_etm^class37Inc,pme_task,RO_state,pme_comdoc,pme_result,pme_subtheme',
            'd1': start_date.format('D/M/YY', formatter='alternative'),
            'd2': end_date.format('D/M/YY', formatter='alternative'),
            'rows': '200',
            'page': '1',
        }
        raw_task_json = self._session.get(CALENDAR_URI, params=calendar_params).json()

        task_info_list = []
        for task in raw_task_json['rows']:
            raw_plan_date, raw_fact_date = task['cell'][1], task['cell'][2]
            plan_date = pendulum.from_format(raw_plan_date, '%d/%m/%y') if raw_plan_date else None
            fact_date = pendulum.from_format(raw_fact_date, '%d/%m/%y') if raw_fact_date else None
            task_info_list.append(TaskInfo(
                id=task['id'], subtheme=task['cell'][0], plan_date=plan_date,
                fact_date=fact_date, type=task['cell'][3], client=task['cell'][4],
                manager=task['cell'][5], task=task['cell'][6], status=task['cell'][7],
                documents=task['cell'][8], result=task['cell'][9], pme_subtheme=task['cell'][10],
            ))
        # Варианты: назначено, выполнено, не выполнено, не зачтено
        if status_filter:
            task_info_list = [task for task in task_info_list if task.status.lower().startswith(status_filter)]
        return task_info_list

    def complete_schedule_task(self,
                               task_id,
                               result_text,
                               fact_date=pendulum.now('Europe/Moscow').format('D/M/YY', formatter='alternative')):
        # fact_date - Pendulum Time Format
        CALENDAR_COMPLETE_TASK_URI = 'http://ipro.etm.ru/cat/runprog.html'
        complete_task_params = {
            'man': self._auth_data._man_id,
            'login': self._auth_data._login,
            'syf_prog': 'pr_meeting-rsp',
            'withoutArchive': 'yes',
            'RSPAction': 'U',
            'idLabel': 'id',
            'id': task_id,
            # 'pme_datep': '14/12/17',
            'pme_state': 'comp_succ',
            'pme_datef': fact_date.format('D/M/YY', formatter='alternative'),
            'pme_result': result_text,
        }
        self._session.get(CALENDAR_COMPLETE_TASK_URI, params=complete_task_params)
        logger.info('Task {} completed'.format(complete_task_params['id']))

    def fill_month_plan_to_client(self, client_id, to_for_month, rtn_for_month, month=None, year=None):
        PLAN_URI = 'http://spb.etm.ru/cat/data-plan.html'
        today = pendulum.now('Europe/Moscow')
        year = year if year else today.year
        month = month if month else today.month

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
