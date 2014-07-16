# -*- coding: utf-8 -*-

import re
import md5
import string
from exceptions import Exception

class TxtHash:
    __id = None
    __hw_type = None
    __regex = None
    __is_id = None
    __digs = None
    __regex_str = "([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})"
    
    def __init__(self, is_id, clientid_or_mac, hw_type):
        self.__id = clientid_or_mac
        self.__hw_type = hw_type
        self.__is_id = is_id
        self.__digs = string.digits + string.lowercase
        self.__regex = re.compile(self.__regex_str, re.IGNORECASE)
    
    # Retorna o valor para o hw_type passado, só da suporte a Ethernet a principio
    def hw_type_to_int(self):
        return {
            'Ethernet': 1,
        }[self.__hw_type]
        
    def __int2base(self, x, base):
        if x < 0:
            sign = -1
        elif x == 0:
            return '0'
        else:
            sign = 1
            
        x *= sign        
        digits = []
        
        while x:
            digits.append(self.__digs[x % base])
            x /= base

        if sign < 0:
            digits.append('-')
        digits.reverse()

        return ''.join(digits)
    
    def __get_prefix(self):
        # Se for 31 indica que usou o campo "Client-Identifier" do DHCP para calcular o HASH
        if self.__is_id:
            return "31"
        else:
            return "00"
        
    def txt(self):
        try:            
            mac_itens = []

            # Pega os elementos do match da expressao regular
            for item in re.finditer(self.__regex, self.__id):
                    for item2 in item.groups():
                            mac_itens.append(item2)
            
            # Pega o valor para o hw_type passado
            decimals = [self.hw_type_to_int()]
            # Converte cada elemento em decimal
            for item in mac_itens:
                a = int(item, 16)
                decimals.append(a)
            
            # Calcula o md5
            m = md5.new()
            m.update(bytearray(decimals))
            
            # Retorna junto com o prefixo
            return self.__get_prefix() + m.hexdigest()           
        except Exception:
            raise Exception("Error calculating TXT hash.")
