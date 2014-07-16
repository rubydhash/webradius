# -*- coding: utf-8 -*-

import psycopg2
import radiusd
import datetime

import datetimeutils

# Busca o ip alocado para um determinado MAC, prove metodos para desalocar o ip também 
class Radippool:
    __id = None
    mac = None
    ip = None
    expiry = None
    calledstationid = None
    __conn = None    
    __get_query = "SELECT id, framedipaddress, expiry_time, calledstationid FROM radippool WHERE pool_key = %s ORDER BY expiry_time DESC LIMIT 1"
    __get_query_ip = "SELECT id, framedipaddress, expiry_time, calledstationid FROM radippool WHERE framedipaddress = %s ORDER BY expiry_time DESC LIMIT 1"
    __update_query = "UPDATE radippool SET expiry_time=%s WHERE id = %s"
    
    def __init__(self, conn, mac):
        self.__conn = conn
        self.mac = mac
        
    def __get_cursor(self):
        if self.__conn is None:
            raise Exception("There is no connection.")
        return self.__conn.cursor()
        
    def __set_attributes(self, data):
        self.__id = data[0][0]
        self.ip = data[0][1]
        self.expiry = data[0][2].strftime('%d-%m-%Y %H:%M:%S')
        self.calledstationid = data[0][3]
        
    def is_static_overlapped(self):
        if self.calledstationid == 'dynamic-static':
            return True
        return False
        
    # Determina se esta expirado com base no compo expiry
    def is_expired(self):
        dt = datetimeutils.DateTimeUtils.mystrptime(self.expiry)
        
        now = datetime.datetime.now()
        if dt <= now:
            return True
        else:
            return False
        
    def load(self):
        cur = self.__get_cursor()
        cur.execute(self.__get_query, (self.mac,))
        data = cur.fetchall()
        
        # Sem resultado retorna falso
        if len(data) < 1:
            return False
        
        self.__set_attributes(data)
        
        return True
    
    def load_by_ip(self, ip):
        if ip is None:
            return False
        
        cur = self.__get_cursor()
        cur.execute(self.__get_query_ip, (ip,))
        data = cur.fetchall()
        
        # Sem resultado retorna falso
        if len(data) < 1:
            return False
        
        self.__set_attributes(data)
        
        return True
    
    # Altera o expiry desse IP atribuido para uma data passada, isso sinaliza ao modulo sqlippool que o IP está disponivel
    def release(self):
        self.expiry = "0001-01-01 00:00:00"
        
        cur = self.__get_cursor()
                        
        try:
            cur.execute(self.__update_query, (self.expiry, self.__id))
        except psycopg2.Error, error:
            radiusd.radlog(radiusd.L_ERR, "Pgsql error: %s" % (error))
            raise Exception("Error saving.")
        except psycopg2.Warning, warning:
            radiusd.radlog(radiusd.L_ERR, "Pgsql warning: %s" % (warning))
        except Exception, error:
            radiusd.radlog(radiusd.L_ERR, "Pgsql unknow error: %s" % (error))
            raise Exception("Error updating.")