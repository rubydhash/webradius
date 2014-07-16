# -*- coding: utf-8 -*-

from psycopg2.pool import ThreadedConnectionPool

# Builder para o pool de conexões
class ConnPoolBuilder:
    conn_pool = None
    
    @classmethod
    def get_conn_pool(cls, min, max, database, user, password, host):
        if cls.conn_pool is None:
            cls.conn_pool = ThreadedConnectionPool(min, max, database=database,
                                                   user=user,
                                                   password=password,
                                                   host=host)
        return cls.conn_pool