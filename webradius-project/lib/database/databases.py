# -*- coding: utf-8 -*-

class Database: 
    def __init__(self,db):
        self.module = None
        self.db = db

    def run(self,sql,type="select"):
        """
          Database execute
        """
        result = []    
        connect = self.module.connect(database=self.db.database,
                                   host=self.db.host,
                                   port=self.db.port,
                                   user=self.db.username,
                                   password=self.db.password)
        cursor = connect.cursor()
        cursor.execute(sql)
        if type == "select":
            columns = tuple( [d[0].decode('utf-8') for d in cursor.description] )
            for row in cursor:
                result.append(dict(zip(columns, row)))
        else:
            connect.commit()
        cursor.close()
        connect.close()
        return result


class PostgreSQL(Database):
    def __init__(self,db):
        import psycopg2
        self.module = psycopg2
        self.db = db

class MSSQL(Database):
    def __init__(self,db):
        import pymssql
        self.module = pymssql
        self.db = db
