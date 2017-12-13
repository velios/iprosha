import argparse
import pprint
from getpass import getpass
from os.path import isfile

import pendulum

from iprosha import AuthSession, AuthDbJson, IProBaseClient, IProExcelClient


def make_cmd_arguments_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', '-s', type=int, help='session-id auth method don\'t need sms. Paste session number value')
    parser.add_argument('--login', '-l', help='login to ipro')
    parser.add_argument('--password', '-p', help='password to ipro(only to test)')
    return parser


if __name__ == '__main__':
    cmd_args_parser = make_cmd_arguments_parser()
    cmd_args = cmd_args_parser.parse_args()
    session_id = cmd_args.session
    login = cmd_args.login
    password = cmd_args.password
    
    try:
        json_db = AuthDbJson()
        if not login:
            login = input('Enter login: ')
        ipro_auth = AuthSession(login, json_db)
        if not session_id:
            if not password:
                password = getpass('Enter password: ')
            ipro_auth.prepare_login_with_sms(password)
            sms = input('Enter sms code: ')
            ipro_auth.login_with_sms(sms)
        else:
            ipro_auth.login_with_session_id(session_id)

        EXCEL_PLAN_FILE = 'test.xlsx'
        excel_iprosha = IProExcelClient(ipro_auth, EXCEL_PLAN_FILE)
        if not isfile(EXCEL_PLAN_FILE):
            excel_iprosha.create_planing_xlsx(EXCEL_PLAN_FILE)
            print('Exit. Need to reinitalize class with {} file'.format(EXCEL_PLAN_FILE))
            exit()
        # res = create_list_of_named_tuples_from_xslx(EXCEL_PLAN_FILE)
        user_tasks = excel_iprosha.fetch_user_tasks('выпол', start_date=pendulum.create(2017, 12, 13), end_date=pendulum.create(2017, 12, 15))
        pprint.pprint([task for task in user_tasks])
        # excel_iprosha.complete_schedule_task('0x00000000024cda87', 'Подписан договор на 2018 год. Поставка на объект Южное Депо!', fact_date=pendulum.create(2017, 12, 14))

    except Exception as e:
        print(e)
