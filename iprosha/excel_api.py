from os.path import isfile

import pendulum

from .utils import (create_list_of_named_tuples_from_xslx,
                    add_new_headers_to_xlsx,
                    save_list_of_named_tuples_to_xlsx,)
from .base_api import IProBaseClient
from .session import AuthSession, logger


class IProExcelClient(IProBaseClient):
    def __init__(self, session: AuthSession, xlsx_filepath):
        super().__init__(session)
        if not isfile(xlsx_filepath):
            logger.error('You {} file is not exist'.format(xlsx_filepath))
        self._xlsx_filepath = xlsx_filepath

    # TODO Experimental проверить в работе
    def fill_schedule(self):  # $("#dialog_delete").dialog("open");
        raw_excel_data = create_list_of_named_tuples_from_xslx(self._xlsx_filepath)
        for item in raw_excel_data:
            formated_date = pendulum.instance(item.task_date).format('D/M/YY', formatter='alternative')
            self.fill_schedule_task(client_id=item.id,
                                    task_date=formated_date,
                                    task_message=item.task_message,
                                    task_result=None,)
        logger.info('Success: tasks from {} transfer is done!'.format(self._xlsx_filepath))
        logger.info('If need to delete smth use $("#dialog_delete").dialog("open"); in js console')

    # TODO Experimental проверить в работе
    def fill_month_plan(self):
        raw_excel_data = create_list_of_named_tuples_from_xslx(self._xlsx_filepath)
        for item in raw_excel_data:
            self.fill_month_plan_to_client(client_id=item.id,
                                           to_for_month=item.to_for_month,
                                           rtn_for_month=item.rtn_for_month,)
        logger.info('Success: month plan from {} transfer is done!'.format(self._xlsx_filepath))

    def create_planing_xlsx(self, output_filepath, overwrite=False):
        if not overwrite:
            if isfile(output_filepath):
                raise Exception('File {} already exist!'.format(output_filepath))
        list_of_named_tuples = self.client_info_list
        save_list_of_named_tuples_to_xlsx(list_of_named_tuples, output_filepath)
        add_new_headers_to_xlsx(output_filepath, ['task_date',
                                                  'task_message',
                                                  'to_for_month',
                                                  'rtn_for_month'])
