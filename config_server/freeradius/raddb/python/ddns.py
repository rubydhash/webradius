# -*- coding: utf-8 -*-
#
# Modulo que controla a inclusão dinâmica no DNS

import radiusd
import psycopg2

import controller
from connpoolbuilder import ConnPoolBuilder
from config import *

# Versão usando o pool, mas está gerando problemas com o dnspython que está apresentando comportanto estranho.
def post_auth_with_pool(p):
    conn_pool = ConnPoolBuilder.get_conn_pool(min_conn, max_conn, db,
                                              db_user_name, db_passwd, db_hostname)
    
    ctl = controller.DdnsController()    
    ctl.initialize(dns_server_ip, dns_key_name, dns_key, dns_ttl, mode)
    conn = None
    
    try:
        conn = conn_pool.getconn()
        ctl.set_conn(conn)
    except psycopg2.pool.PoolError:
        # Nesse caso não tem uma conexão livre no pool, vamos conectar manualmente
        ctl.connect(db, db_user_name, db_passwd, db_hostname)
    
    reply_tuple = ctl.process(p)
    
    # Se a conexão foi feita para esta requisição fecha ela nesse momento
    ctl.finish()
    
    # Se a conexão veio do Pool vamos devolver para ele
    if conn is not None:
        conn_pool.putconn(conn)
    
    return radiusd.RLM_MODULE_OK, reply_tuple, None

# Versão sem usar pool de coneões que cria uma conexão para cada requisição
def post_auth_without_pool(p):    
    ctl = controller.DdnsController()
    
    ctl.initialize(dns_server_ip, dns_key_name, dns_key, dns_ttl, mode)
    ctl.connect(db, db_user_name, db_passwd, db_hostname)
    
    reply_tuple = ctl.process(p)
        
    ctl.finish()
    
    return radiusd.RLM_MODULE_OK, reply_tuple, None

def instantiate(p):
    # Faz essa chamada só para inicializar as conexões do Pool
    conn_pool = ConnPoolBuilder.get_conn_pool(min_conn, max_conn, db,
                                              db_user_name, db_passwd, db_hostname)

def post_auth(p):
    # Usando a versão sem pool pois a versão com pool está gerando problemas
    return post_auth_without_pool(p)

def detach(p):
    conn_pool = ConnPoolBuilder.get_conn_pool(min_conn, max_conn, db,
                                              db_user_name, db_passwd, db_hostname)
    conn_pool.closeall()
    return radiusd.RLM_MODULE_OK

