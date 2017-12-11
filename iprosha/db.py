import json

class AuthDbAbstract:
    def is_exist_by_login(self, login):
        raise NotImplementedError()
        
    def get_by_login(self, login):
        raise NotImplementedError()
        
    def set_by_login(self, login, data):
        raise NotImplementedError()
        
class AuthDbJson:
    def __init__(self, json_db_filepath='db.json'):
        self.db_path = json_db_filepath
        try:
            with open(self.db_path, 'r') as file_handler:
                pass
        except FileNotFoundError:
            with open(self.db_path, 'w') as file_handler:
                json.dump({}, file_handler)
                
    def is_exist_by_login(self, login_key):
        with open(self.db_path, 'r') as file_handler:
            db_data = json.load(file_handler)
        return login_key in db_data.keys()
    
    def get_by_login(self, login_key):
        with open(self.db_path, 'r') as file_handler:
            db_data = json.load(file_handler)
        return db_data.get(login_key, None)
        
    def set_by_login(self, login_key, **data):
        with open(self.db_path, 'r') as file_handler:
            db_data = json.load(file_handler)
        db_data[login_key] = data
        with open(self.db_path, 'w') as file_handler:
            json.dump(db_data, file_handler)
