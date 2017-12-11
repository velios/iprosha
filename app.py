import logging
import argparse
import json
from collections import namedtuple
import re
import pprint
import pickle

import requests
from openpyxl import Workbook, load_workbook
from bs4 import BeautifulSoup

from iprosha import IProAuthSession, AuthDbJson


def make_cmd_arguments_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', '-s', type=int, help='session-id auth method don\'t need sms. Paste session number value')
    return parser


if __name__ == '__main__':
    cmd_args_parser = make_cmd_arguments_parser()
    cmd_args = cmd_args_parser.parse_args()
    session_id = cmd_args.session
    
    try:
        db = AuthDbJson()
        auth = IProAuthSession('07elv', db)
        auth.prepare_login_with_sms('d561tj5222')
        sms = input('Sms code: ')
        auth.login_with_sms(sms)
    except Exception as e:
        print(e)
    

    # ipro_session, ipro_auth_info = get_ipro_auth_session(login=login,
    #                                                      password=password,
    #                                                      session_id=session_id,)

    # pprint.pprint(ipro_auth_info)

    #full_client_list = fetch_full_client_list(session=ipro_session,
    #                                          session_info=ipro_auth_info,
    #                                          url_id_parameter=1461219847 #07see
                                              #url_id_parameter=1461216007 #07elv
    #                                          )
    #save_list_of_named_tuples_to_xlsx(list_of_named_tuples=full_client_list,
    #                                  output_filepath='full_client_list_{}.xlsx'.format(login))
    # fill_schedule(session=ipro_session,
    #               session_info=ipro_auth_info,
    #               schedule_file='full_client_list_07see_november.xlsx',)
    #setup_plan_to_company(session=ipro_session,
    #                      session_info=ipro_auth_info,
    #                      company_id='60115193',
    #                      to_for_month='0',
    #                      rtn_for_month='0.00')
