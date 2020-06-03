from excepions import *
from config import DATABASE


class TechDataBase:

    def __init__(self, mysql, table: str = None):
        self._mysql = mysql
        self._cursor = self._mysql.connection.cursor()
        self._table = table
        result = self._cursor.execute(f"CHECK TABLE {self._table}")
        if result == 2:
            self.createTable(self._table)

    def createTable(self, table: str):
        if not table:
            raise TableIsMissing()

        if table == "user":
            self._cursor.execute("CREATE TABLE user (user_id MEDIUMINT(6) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT, username VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, PRIMARY KEY( id ) USING BTREE)")
        elif table == "user_key":
            self._cursor.execute(f"CREATE TABLE user_key (username VARCHAR(255) NOT NULL, user_key VARCHAR(255) NOT NULL, PRIMARY KEY( username ) USING BTREE, CONSTRAINT username FOREIGN KEY (username) REFERENCES {DATABASE}.users (username) ON UPDATE NO ACTION ON DELETE NO ACTION)")
        elif table == "password_recovery":
            self._cursor.execute(f"CREATE TABLE password_recovery (user_id MEDIUMINT(6) UNSIGNED ZEROFILL NOT NULL, access_hash VARCHAR(100) NOT NULL, expires DATETIME NOT NULL, PRIMARY KEY (user_id) USING BTREE, CONSTRAINT user_id_key FOREIGN KEY (user_id) REFERENCES {DATABASE}.users (id) ON UPDATE NO ACTION ON DELETE NO ACTION)")
        else:
            self._cursor.execute(f"CREATE TABLE {table} (name VARCHAR(255) NOT NULL, number VARCHAR(255) NOT NULL)")
        self._mysql.connection.commit()
        self._table = table

    def deleteTable(self, table: str):
        if not table:
            raise TableIsMissing()

        self._cursor.execute(f"DROP TABLE {table}")

    def getAllValue(self):
        if self._table:
            self._cursor.execute(f"SELECT * FROM {self._table}")
            rows = self._cursor.fetchall()
            return rows

        raise TableIsMissing()

    def getAllDesc(self):
        if self._table:
            self._cursor.execute(f"SELECT * FROM {self._table}")
            desc = self._cursor.description
            return desc

        raise TableIsMissing()

    def getCol(self, col_name: str):
        if self._table:
            self._cursor.execute(f"SELECT {col_name} FROM {self._table}")
            col = self._cursor.fetchall()
            return col

        raise TableIsMissing()

    def getRow(self, col_name: str, name: str):
        if self._table:
            self._cursor.execute(f"SELECT * FROM {self._table} WHERE {col_name}='{name}'")
            row = self._cursor.fetchall()
            if len(row) == 0:
                return "null"
            return row[0]

        raise TableIsMissing()

    def addSomeRow(self, col: tuple, val: tuple):
        if not self._table:
            raise TableIsMissing()

        col = str(col).replace('\'', '')
        val = str(val)
        self._cursor.execute(f"INSERT INTO {self._table} {col} VALUES {val}")

    def addVal(self, col: str, val: str):
        if not self._table:
            raise TableIsMissing()

        self._cursor.execute(f"INSERT INTO {self._table} {col} VALUES {val}")

    def updateRow(self, col_name: str, val: str, elemid: str, elemval: str):
        if not self._table:
            raise TableIsMissing()

        self._cursor.execute(f"UPDATE {self._table} SET {col_name}='{val}' WHERE {elemid}='{elemval}'")

    def delRow(self, col_name: str, val: str):
        if not self._table:
            raise TableIsMissing()

        self._cursor.execute(f"DELETE FROM {self._table} WHERE {col_name}='{val}'")

    def delRowByCond(self, condition: str):
        if not self._table:
            raise TableIsMissing()

        self._cursor.execute(f"DELETE FROM {self._table} WHERE {condition}")
