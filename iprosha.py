import logging
import argparse
import json
from collections import namedtuple
import re
import pprint

import requests
from openpyxl import Workbook, load_workbook
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logger = logging.getLogger()


def make_cmd_arguments_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', '-s', type=int, help='session-id auth method don\'t need sms. Paste session number value')
    return parser


def get_ipro_auth_session(login, password, session_id=None):
    session = requests.Session()
    man_id, login_type = '9019820', 'WI'
    login_with_sms_url = 'https://spb.etm.ru/ns2000/data-login.php'
    login_without_sms_url = 'http://spb.etm.ru/ipro2'
    if session_id:
        request_params = {
            'login': login,
            'session': session_id,
            'man-id': man_id,
            'login_type': login_type
        }
        session.get(login_without_sms_url, params=request_params)
        logger.info('You authorise with exist session-id: {}'.format(session_id))
    else:
        request_params = {
            't': 'login',
            'log': login,
            'pwd': password
        }
        session_params_json = session.get(login_with_sms_url, params=request_params).json()
        session_id = session_params_json.get('session')
        man_id = session_params_json.get('man_id')
        login_type = session_params_json.get('login_type')
        sms_code = input('Please type sms code here: ')
        request_params['smsCode'], request_params['session'] = sms_code, session_id
        session.get(login_with_sms_url, params=request_params)
        logger.info('You authorise! You man-id: {}'.format(man_id))
        logger.info(' You session-id: {}'.format(session_id))
        logger.info(' You login-type: {}'.format(login_type))
    return session


def clean_html_tags(cleaned_text):
    return BeautifulSoup(cleaned_text, "html.parser").text


def fetch_full_client_list(session):
    client_info_page_url = 'http://spb.etm.ru/cat/data-orgtree.html?login=07elv&man=9019820&id=1461216007&d1=01/09/17&d2=01/10/17'
    client_info_page_html = session.get(client_info_page_url).text
    client_info_json = json.loads(client_info_page_html)['Nodes']
    ClientInfo = namedtuple('ClientInfo', ['id', 'name', 'specialization', 'worth', 'warm'])
    result = []
    for client_info in client_info_json:
        client_id = client_info['ID']
        name, specialization, worth, warm = re.match(r'(.+) \((\S+),~(\S+), +(.+)\)', client_info['Name']).groups()
        result.append(ClientInfo(
            id=client_id,
            name=clean_html_tags(name),
            specialization=specialization,
            worth=worth,
            warm=warm
        ))
    return result


def save_list_of_named_tuples_to_xlsx(list_of_named_tuples, output_filepath):
    if not list_of_named_tuples:
        raise ValueError('You need put some data to write')
    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet()
    worksheet.append(list_of_named_tuples[0]._fields)
    for named_tuple in list_of_named_tuples:
        worksheet.append(named_tuple)
    workbook.save(output_filepath)


def fill_schedule_task(session, client_code, task_date, task_message):
    client_schedule_post_url = 'http://ipro.etm.ru/cat/runprog.html'
    schedule_request_params = {
        'man': '9019820',
        'login': '07elv',
        'syf_prog': 'pr_meeting-rsp',
        'withoutArchive': 'yes',
        'RSPAction': 'A',
        'pme_persons': 'pmp_class37^ССПб3$man-code^9019820$cli-code^{}$exm_mancode^'.format(client_code),
        'pme_datep': task_date,
        'RO_theme': 'Развитие продаж',
        'pme_theme': 'ВТ10',
        'RO_subtheme': 'Встречи с партнёрами',
        'pme_subtheme': 'ВТ1010',
        'RO_type': 'Встреча с партнёром',
        'pme_type': 'ВМ10',
        'pme_task': task_message,
        'pme_state': 'appoint'
    }
    session.get(client_schedule_post_url, params=schedule_request_params)


def fill_schedule(session, schedule_file): # $("#dialog_delete").dialog("open");
    workbook = load_workbook(filename=schedule_file)
    worksheet = workbook.worksheets[0]
    schedule_file_data = []
    for row_index in range(2, worksheet.max_row):
        data = []
        for cell in worksheet[row_index]:
            data.append(cell.value)
        schedule_file_data.append(data)
    for task in schedule_file_data:
        client_code = task[0]
        task_date = task[2]
        task_message = task[3]
        fill_schedule_task(session, client_code, task_date, task_message)


if __name__ == '__main__':
    login, password = '07elv', 'd561tj4'
    cmd_args_parser = make_cmd_arguments_parser()
    cmd_args = cmd_args_parser.parse_args()
    session_id = cmd_args.session

    ipro_session = get_ipro_auth_session(login, password, session_id=session_id)

    pprint.pprint(fetch_full_client_list(ipro_session))
    # save_list_of_named_tuples_to_xlsx(list_of_named_tuples=fetch_full_client_list(ipro_session),
    #                                   output_filepath='named_tuple.xlsx')
    # pprint.pprint(fill_schedule(ipro_session, 'task2.xlsx'))