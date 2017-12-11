import argparse
from os.path import isfile

from iprosha import AuthSession, AuthDbJson, IProBaseClient, IProExcelClient
from iprosha.utils import (create_list_of_named_tuples_from_xslx,
                           add_new_headers_to_xlsx,
                           save_list_of_named_tuples_to_xlsx)


def make_cmd_arguments_parser():
    parser = argparse.ArgumentParser()
    # TODO добавить логин через консоль
    parser.add_argument('--session', '-s', type=int, help='session-id auth method don\'t need sms. Paste session number value')
    return parser


def create_planing_xlsx(xlsx_filepath, iprosha: IProBaseClient, overwrite=False):
    if not overwrite:
        if isfile(xlsx_filepath):
            raise Exception('File {} already exist!'.format(xlsx_filepath))
    list_of_named_tuples = iprosha.full_client_list
    save_list_of_named_tuples_to_xlsx(list_of_named_tuples, xlsx_filepath)
    add_new_headers_to_xlsx(xlsx_filepath, ['task_date',
                                            'task_message',
                                            'to_for_month',
                                            'rtn_for_month'])


if __name__ == '__main__':
    cmd_args_parser = make_cmd_arguments_parser()
    cmd_args = cmd_args_parser.parse_args()
    session_id = cmd_args.session
    
    try:
        json_db = AuthDbJson()
        login = input('Enter login: ')
        ipro_auth = AuthSession(login, json_db)
        if not session_id:
            # TODO если данные есть в базе чтобы не запрашивал пароль
            password = input('Enter password: ')
            ipro_auth.prepare_login_with_sms(password)
            sms = input('Enter sms code: ')
            ipro_auth.login_with_sms(sms)
        else:
            ipro_auth.login_with_session_id(session_id)

        # iprosha = IProBaseClient(ipro_auth)
        # excel_iprosha = IProExcelClient(ipro_auth, 'test.xlsx')
        # list_of_named_tuples = iprosha.full_client_list
        # create_planing_xlsx('test.xlsx', excel_iprosha)
        # res = create_list_of_named_tuples_from_xslx('test.xlsx')
        # print(res)
        # excel_iprosha.fill_schedule()

    except Exception as e:
        print(e)


    # fill_schedule(session=ipro_session,
    #               session_info=ipro_auth_info,
    #               schedule_file='full_client_list_07see_november.xlsx',)
    #setup_plan_to_company(session=ipro_session,
    #                      session_info=ipro_auth_info,
    #                      company_id='60115193',
    #                      to_for_month='0',
    #                      rtn_for_month='0.00')
