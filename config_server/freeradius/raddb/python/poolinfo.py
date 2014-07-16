# -*- coding: utf-8 -*-

# Carrega as informações do pool com base no MAC ou no gateway. 
class Poolinfo:
    __id = None
    pool_name = None
    domain_name = None
    rev_domain_name = None
    lease_time = None
    __conn = None    
    __get_query_by_mac = "SELECT id, pool_name, description, mask, router_address," \
                         "domain_name, rev_domain_name, dns_server," \
                         "dns_server2, netbios, netbios_name_server, mtu, ntp_server," \
                         "lease_time, root_path, boot_filename, init_address, end_address " \
                         "FROM poolinfo WHERE pool_name = " \
                         "(SELECT value FROM radcheck WHERE username = %s " \
                         "and attribute = 'Pool-Name') LIMIT 1"
    __get_query_by_gw = "SELECT id, pool_name, description, mask, router_address, domain_name," \
                        "rev_domain_name, dns_server, dns_server2, netbios, netbios_name_server," \
                        "mtu, ntp_server, lease_time, root_path, boot_filename, init_address," \
                        "end_address FROM poolinfo WHERE %s = ANY(bind_gateways) LIMIT 1;"
    
    def __init__(self, conn):
        self.__conn = conn
        
    def __get_cursor(self):
        if self.__conn is None:
            raise Exception("There is no connection.")
        return self.__conn.cursor()
        
    def __set_attributes(self, data):
        self.__id = data[0][0]
        self.pool_name = data[0][1]
        self.domain_name = data[0][5]
        self.rev_domain_name = data[0][6]
        self.lease_time = data[0][13]
        
    def load_by_mac(self, mac):
        cur = self.__get_cursor()
        cur.execute(self.__get_query_by_mac, (mac,))        
        data = cur.fetchall()
        
        # Sem resultado retorna falso
        if len(data) < 1:
            return False
        
        self.__set_attributes(data)
        
        return True
    
    def load_by_gw(self, gw):
        cur = self.__get_cursor()
        cur.execute(self.__get_query_by_gw, (gw,))        
        data = cur.fetchall()
        
        # Sem resultado retorna falso
        if len(data) < 1:
            return False
        
        self.__set_attributes(data)
        
        return True