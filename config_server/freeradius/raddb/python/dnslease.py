# -*- coding: utf-8 -*-

import psycopg2
import datetime

import datetimeutils

from exceptions import Exception

# Entrada na tabela que controla se já existe um registro 
class DdnsLease:
    __id = None
    expiry = None
    mac = ""
    ip = None
    hostname = None
    fwd_name = None
    rev_name = None
    rev_domain = None
    hw_type = None
    txt = None
    __conn = None
    __get_all_expired = "SELECT id, expiry, mac, ip, hostname, fwd_name, txt, rev_name, rev_domain, hw_type from ddns WHERE expiry <= %s;"
    __get_query_fwd = "SELECT id, expiry, mac, ip, hostname, fwd_name, txt, rev_name, rev_domain, hw_type FROM ddns WHERE fwd_name = %s LIMIT 1"
    __get_query_ip = "SELECT id, expiry, mac, ip, hostname, fwd_name, txt, rev_name, rev_domain, hw_type FROM ddns WHERE ip = %s LIMIT 1"
    __insert_query = "INSERT INTO ddns (expiry, mac, ip, hostname, fwd_name, txt, rev_name, rev_domain, hw_type) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    __update_query = "UPDATE ddns SET expiry=%s, mac=%s, ip=%s, hostname=%s, fwd_name=%s, txt=%s, rev_name=%s, rev_domain=%s, hw_type=%s WHERE id = %s"
    __delete_query = "DELETE FROM ddns WHERE id = %s"
    
    def __init__(self, conn, values=None):
        self.__conn = conn
        if values is not None:
            self.__set_attributes(values)
        
    def __get_cursor(self):
        if self.__conn is None:
            raise Exception("There is no connection.")
        return self.__conn.cursor()

    def __set_attributes(self, data):
        self.__id = data[0]
        self.expiry = data[1].strftime('%d-%m-%Y %H:%M:%S')
        self.mac = data[2]
        self.ip = data[3]
        self.hostname = data[4]
        self.fwd_name = data[5]
        self.txt = data[6]
        self.rev_name = data[7]
        self.rev_domain = data[8]
        self.hw_type = data[9]
        
    def create_fwd_name(self, hostname, domain):
        if domain[-1] == '.':
            domain = domain[:-1]
        if hostname[-1] == '.':
            hostname = hostname[:-1]
            
        return hostname + '.' + domain
    
    @classmethod
    def load_all_expired(cls, conn, rotate_date):
        cur = conn.cursor()
        cur.execute(cls.__get_all_expired, (rotate_date,))
        data = cur.fetchall()
        
        result = []
        count = 0
        
        for lease in data:
            result.append(DdnsLease(conn, data[count]))
            count = count + 1
        
        return result

    def load_by_fwd(self, hostname, domain):
        cur = self.__get_cursor()
        cur.execute(self.__get_query_fwd, (self.create_fwd_name(hostname, domain),))
        data = cur.fetchall()
        
        # Sem resultado retorna falso
        if len(data) < 1:
            return False
        
        self.__set_attributes(data[0])
        
        return True
    
    def load_by_ip(self, ip):
        cur = self.__get_cursor()
        cur.execute(self.__get_query_ip, (ip,))
        data = cur.fetchall()
        
        # Sem resultado retorna falso
        if len(data) < 1:
            return False
        
        self.__set_attributes(data[0])
        
        return True
    
    def delete(self):
        if self.__id is None:
            raise Exception("DdnsLease without id cannot be deleted.")
        
        cur = self.__get_cursor()
        
        try:
            cur.execute(self.__delete_query, (self.__id,))
        except psycopg2.Error, error:
            raise Exception("Error deleting: %s" % (error))
#         except psycopg2.Warning, warning:
#             print "Pgsql warning: %s" % (error)
#         except Exception, error:
#             print "Pgsql unknow error: %s" % (error)

    # Determina se esta expirado com base no compo expiry
    def is_expired(self):
        dt = datetimeutils.DateTimeUtils.mystrptime(self.expiry)
        now = datetime.datetime.now()
        if dt <= now:
            return True
        else:
            return False
        
    def __validate_attributes(self, insert=False):
        if not insert and self.__id is None:
            raise Exception("DdnsLease without id cannot be saved.")
        
        if self.expiry is None or self.expiry == '':
            raise Exception("Attribute None.")
        if self.mac is None or self.mac == '':
            raise Exception("Attribute None.")
        if self.ip is None or self.ip == '':
            raise Exception("Attribute None.")
        if self.hostname is None or self.hostname == '':
            raise Exception("Attribute None.")
        if self.fwd_name is None or self.fwd_name == '':
            raise Exception("Attribute None.")        
        if self.hw_type is None or self.hw_type == '':
            raise Exception("Attribute None.")
        if self.txt is None or self.txt == '':
            raise Exception("Attribute None.")
        
        # Os atributos a seguir podem ser nulos
        if self.rev_name is None:
            self.rev_name = ''
        if self.rev_domain is None:
            self.rev_domain = ''
        
    def save(self, insert=False):
        self.__validate_attributes(insert)
        
        cur = self.__get_cursor()
                        
        try:
            if insert:
                cur.execute(self.__insert_query, (self.expiry, self.mac, self.ip,
                                                  self.hostname, self.fwd_name,
                                                  self.txt, self.rev_name,
                                                  self.rev_domain, self.hw_type))
            else:
                cur.execute(self.__update_query, (self.expiry, self.mac, self.ip,
                                                  self.hostname, self.fwd_name,
                                                  self.txt, self.rev_name,
                                                  self.rev_domain, self.hw_type,
                                                  self.__id))
        except psycopg2.Error, error:
            raise Exception("Error saving: %s" % (error))
#         except psycopg2.Warning, warning:
#             print "Pgsql warning: %s" % (error)
#         except Exception, error:
#             print "Pgsql unknow error: %s" % (error)
        
    # Calcula o domain com base no hostname e fwd_name
    def domain(self):
        if not self.fwd_name.startswith(self.hostname):
            raise Exception("Invalid Forward name.")
        result = self.fwd_name.partition(self.hostname)
        
        if len(result) < 3:
            raise Exception("Invalid Forward name.")
        
        domain = result[2]
        
        if domain[0] == '.':
            return domain[1:]
        return domain

    def __unicode__(self):
        return "Id:%s Hostname:%s MAC:%s IP:%s Fwd Name:%s Rev Name:%s  Rev domain:%s" % (self.__id, self.hostname, self.mac, self.ip, self.fwd_name, self.rev_name, self.rev_domain)
        
    def __str__(self):
        return unicode(self).encode('utf-8')