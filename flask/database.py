import os
import time
from datetime import datetime
import mariadb as sql

########## CONFIGURE ##########
HOST="localhost"
USERNAME="root"
PASSWORD=""
DATABASE="info_caseopening"
########## CONFIGURE ##########

connection = {
    "user": os.environ.get('MARIADB_USER', USERNAME),
    "password": os.environ.get('MARIADB_PASSWORD', PASSWORD),
    "host": os.environ.get('MARIADB_HOST', HOST),
    "database": os.environ.get('MARIADB_DB', DATABASE)
}

########## DATABASE MANAGEMENT SYSTEM ##########
class dbms:
    def __init__(self):
        self.conn = sql.connect(user=connection["user"], password=connection["password"], host=connection["host"], database=connection["database"])
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
    
    def createTables(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Users (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            Username TEXT NOT NULL UNIQUE,
            Displayname TEXT NOT NULL,
            UserID INT NOT NULL,
            Created TEXT NOT NULL,
            PasswordHash TEXT NOT NULL,
            Cases INT NOT NULL,
            Logins INT NOT NULL,
            FailedLogins INT NOT NULL);""")
        
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Sessions (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            SessionKey TEXT NOT NULL,
            UserID INT NOT NULL,
            Accessed INT NOT NULL,
            Duration INT NOT NULL);""")
        
        self.cur.execute("""CREATE TABLE IF NOT EXISTS History (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            UserID INT NOT NULL,
            WonRarity TEXT NOT NULL,
            WonName TEXT NOT NULL,
            WonDisplay TEXT NOT NULL,
            WonDate TEXT NOT NULL);""")
    
    def get_passhash(self, username: str):
        self.cur.execute(f"SELECT ID, PasswordHash FROM Users WHERE Username='{username}' OR Displayname='{username}'")

        result = self.cur.fetchone()

        if not result:
            return False, "Dieser Benutzername konnte nicht gefunden werden.", None
        else:
            return True, result[0], result[1]
    
    def delete_account(self, userid: int):
        self.cur.execute(f"DELETE FROM Users WHERE UserID='{userid}'")
        self.cur.execute(f"DELETE FROM Sessions WHERE UserID='{userid}'")
        self.cur.execute(f"DELETE FROM History WHERE UserID='{userid}'")

    def check_sesskey(self, sesskey:str):
        self.cur.execute(f"SELECT SessionKey, UserID, Accessed, Duration FROM Sessions WHERE SessionKey='{sesskey}'")
        entry=self.cur.fetchone()
        if entry and sesskey in entry and time.time() < entry[2]+entry[3]:
            return True, entry[1]
        else:
            return False, "Bitte schließe deine Sitzung und versuche es erneut."

    def get_cases(self, userid: int):
        self.cur.execute(f"SELECT Cases FROM Users WHERE UserID='{userid}'")

        result = self.cur.fetchone()

        if result:
            return result[0]
        else:
            return None
        
    def get_logins(self, userid: int):
        self.cur.execute(f"SELECT Logins FROM Users WHERE UserID='{userid}'")

        result = self.cur.fetchone()

        if result:
            return result[0]
        else:
            return None
        
    def get_failed_logins(self, userid: int):
        self.cur.execute(f"SELECT FailedLogins FROM Users WHERE UserID='{userid}'")

        result = self.cur.fetchone()

        if result:
            return result[0]
        else:
            return None

    def get_passhash_for_user(self, userid: int):
        self.cur.execute(f"SELECT PasswordHash FROM Users WHERE UserID='{userid}'")

        result = self.cur.fetchone()

        if result:
            return result[0]
        else:
            return None
        
    def fetch_user_data(self, trait):
        if isinstance(trait, int):
            replace_argument = f"ID={trait}"
        elif isinstance(trait, str):
            replace_argument = f"Username='{trait}'"
        else:
            return False, "Dieser Typ ist ungültig."

        self.cur.execute(f"SELECT * FROM Users WHERE {replace_argument}")

        account = self.cur.fetchone()

        if not account or len(account) <= 0:
            return False, "Der Benutzer wurde nicht gefunden."
        else:
            return True, account

    def get_passhash_for_username(self, username: str):
        self.cur.execute(f"SELECT PasswordHash FROM Users WHERE Username='{username}' OR Displayname='{username}'")

        result = self.cur.fetchone()

        if result:
            return result[0]
        else:
            return None
        
    def exist_username(self, username: str):
        self.cur.execute(f"SELECT * FROM Users WHERE Username='{username}' OR Displayname='{username}'")

        result = self.cur.fetchone()

        if result:
            return True
        else:
            return False

    def get_userid_by_session_key(self, session_key: str):
        self.cur.execute(f"SELECT UserID FROM Sessions WHERE SessionKey='{session_key}'")

        result = self.cur.fetchone()

        if result:
            return result[0]
        else:
            return None
        
    def get_userid_by_username(self, username: str):
        self.cur.execute(f"SELECT UserID FROM Users WHERE Username='{username}' OR Displayname='{username}'")

        result = self.cur.fetchone()

        if result:
            return result[0]
        else:
            return None

    def remove_case(self, userid: int):
        current_cases = self.get_cases(userid)

        if current_cases is not None and current_cases > 0:
            new_cases = current_cases - 1

            self.cur.execute(f"UPDATE Users SET Cases={new_cases} WHERE UserID='{userid}'")
        
    def add_login(self, userid: int):
        current_logins = self.get_logins(userid)

        if current_logins is not None:
            new_logins = current_logins + 1

            self.cur.execute(f"UPDATE Users SET Logins={new_logins} WHERE UserID='{userid}'")
        
    def add_failed_login(self, userid: int):
        current_failed_logins = self.get_failed_logins(userid)

        if current_failed_logins is not None:
            new_failed_logins = current_failed_logins + 1

            self.cur.execute(f"UPDATE Users SET FailedLogins={new_failed_logins} WHERE UserID='{userid}'")
        
    def update_password(self, userid: int, passhash: str):
        self.cur.execute(f"UPDATE Users SET PasswordHash='{passhash}' WHERE UserID='{userid}'")

    def update_nickname(self, userid: int, nickname: str):
        self.cur.execute(f"UPDATE Users SET Displayname='{nickname}' WHERE UserID='{userid}'")

    def set_sesskey(self, sesskey:str, userid: int, lifetime: int):
        self.cur.execute(f"INSERT INTO Sessions (SessionKey, UserID, Accessed, Duration) VALUES('{sesskey}', {userid}, {time.time()}, {lifetime})")

    def add_history(self, userid: int, wonrarity: str, wonname: str, wondisplay: str):
        self.cur.execute(f"INSERT INTO History (UserID, WonRarity, WonName, WonDisplay, WonDate) VALUES ({userid}, '{wonrarity}', '{wonname}', '{wondisplay}', '{datetime.now().strftime('%d.%m.%y')}')") # time: %H:%M:%S   
    
    def logout_user(self, sesskey:str):
        self.cur.execute(f"DELETE FROM Sessions WHERE SessionKey='{sesskey}'")

    def get_user_history(self, userid: int):
        self.cur.execute(f"SELECT History.ID, History.WonRarity, History.WonName, History.WonDisplay, History.WonDate FROM Users INNER JOIN History ON Users.UserID = History.UserID WHERE Users.UserID='{userid}'")

        entries = self.cur.fetchall()
        total_count = len(entries)
        entries_exist = total_count > 0

        return entries, total_count, entries_exist
########## DATABASE MANAGEMENT SYSTEM ##########

if __name__ == "__main__":
    dbms = dbms(connection)
    dbms.cur.close()
    dbms.conn.close()
    exit()