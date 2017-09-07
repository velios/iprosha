import logging
import argparse
import json
from collections import namedtuple
import re
import pprint

import requests
from openpyxl import load_workbook
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logger = logging.getLogger()


def make_cmd_arguments_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', '-s', type=int, help='session-id auth method don\'t need sms. Paste session number value')
    return parser.parse_args()


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
        session_id = session.get(login_with_sms_url, params=request_params).json().get('session')
        sms_code = input('Please type sms code here: ')
        request_params['smsCode'], request_params['session'] = sms_code, session_id
        session.get(login_with_sms_url, params=request_params)
        logger.info('You authorise! You session-id: {}'.format(session_id))
    return session


def fetch_full_client_list(session):
    client_info_page_url = 'http://spb.etm.ru/cat/data-orgtree.html?login=07elv&man=9019820&id=1461216007&d1=01/09/17&d2=01/10/17'
    client_info_page_html = session.get(client_info_page_url).text
    client_info_json = json.loads(client_info_page_html)['Nodes']
    ClientInfo = namedtuple('ClientInfo', ['id', 'name', 'specialization', 'worth', 'warm'])
    result = []
    for client_info in client_info_json:
        client_id = client_info['ID']
        name, specialization, worth, warm = re.match(r'(.+) \((\S+),~(\S+), +(.+)\)', client_info['Name']).groups()
        result.append(ClientInfo(client_id, name, specialization, worth, warm))
    return result


def fill_shedule(session, schedule_file): # $("#dialog_delete").dialog("open");
    workbook = load_workbook(filename=schedule_file)
    worksheet = workbook.worksheets[0]
    schedule_file_data = []
    for row_index in range(2,worksheet.max_row):
        data = []
        for cell in worksheet[row_index]:
            data.append(cell.value)
        schedule_file_data.append(data)
    return schedule_file_data



if __name__ == '__main__':
    login, password = '07elv', 'd561tj3'
    cmd_args = make_cmd_arguments_parser()
    session_id = cmd_args.session
    ipro_session = get_ipro_auth_session(login, password, session_id=session_id) if session_id \
        else get_ipro_auth_session(login, password)

    # pprint.pprint(fetch_full_client_list(ipro_session))
    pprint.pprint(fill_shedule(ipro_session, 'task2.xlsx'))