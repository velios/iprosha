import pendulum

from .utils import create_list_of_named_tuples_from_xslx
from .base_api import IProBaseClient
from .session import AuthSession


class IProExcelClient(IProBaseClient):
    def __init__(self, session: AuthSession, xlsx_filepath):
        super().__init__(session)
        self._xlsx_filepath = xlsx_filepath

    def fill_schedule(self):  # $("#dialog_delete").dialog("open");
        raw_excel_data = create_list_of_named_tuples_from_xslx(self._xlsx_filepath)
        pendulum.set_formatter('alternative')
        for item in raw_excel_data[:5]:
            formated_date = pendulum.instance(item.task_date).format('D/M/YY')
            self.fill_schedule_task(client_id=item.id,
                                    task_date=formated_date,
                                    task_message=item.task_message,
                                    task_result=None,)
