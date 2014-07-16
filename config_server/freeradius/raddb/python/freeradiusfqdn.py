# -*- coding: utf-8 -*-

import re
from exceptions import Exception

# Classe que representa um campo do tipo FQDN com base no campo recebido do Freeradius, 81
class FreeradiusFqdn:
    __raw_fqdn = ""
    dont_update = False
    server_update_a = False
    server_override = False
    ascii_encoding = False
    fqdn = ""
    __regex_str = "\\\(.{3})\\\(.{3})\\\(.{3})(.*)"
    __regex_compiled = None
    
    def __init__(self, raw_fqdn):
        self.__compile_regex()
        self.set_fqdn(raw_fqdn)
        
    def __compile_regex(self):
        if self.__regex_compiled is None:
            self.__regex_compiled = re.compile(self.__regex_str)
            
    def __get_bin(self, num):
        binnum = bin(num)[2:]
        
        if len(binnum) >= 4:
            return binnum
        
        while len(binnum) < 4:
            binnum = '0' + binnum
        
        return binnum
            
    def set_fqdn(self, raw_fqdn):
        self.__raw_fqdn = raw_fqdn
        
        result = re.findall(self.__regex_compiled, self.__raw_fqdn)
        
        if len(result) < 1:
            raise Exception("Invalid Raw FQDN")
        if len(result[0]) < 4:
            raise Exception("Invalid Raw FQDN")
        
        # Pega a string de FQDN
        self.fqdn = result[0][3]
        
        # Converte as opcoes dos bits para inteiro para depois converter para binário
        # Cuidado pois vem em base 8
        integer_option = int(result[0][0], 8)
        # Converte para binário
        binary = self.__get_bin(integer_option)
        
        if len(binary) < 4:
            raise Exception("Invalid Raw FQDN")
        
        # Só me interessa os ultimo 4 bits, se tiver mais que isso provavelmente ta errado
        
        # O ultimo bit indica se o servidor deve ou não atualizar as entradas do tipo A
        if binary[-1] == '1':
            self.server_update_a = True
        else:
            self.server_update_a = False

        # O penultimo bit indica se o servidor mudou algum bit ao enviar a resposta. Sempre vem como zero.
        self.server_override = False
        
        # O antepenultimo bit indica  se a codificação do FQDN é ASCII ou "cononical wire format"
        # Não vou tratar se não for ASCII por enquanto
        if binary[-3] == '1':
            raise Exception("Non ASCII encoding in FQDN not yet implemented")
            self.ascii_encoding = False
        else:
            self.ascii_encoding = True
            
        # O primeiro bit indica se o servidor não deve fazer atualização nenhuma entrada incluindo registos A e PTR
        if binary[-4] == '1':
            self.dont_update = True
        else:
            self.dont_update = False

    # Resposta para configuração no modo 'deny'
    # Não vai ser implementado a princípio
    def get_ignore_answer(self):
        raise Exception("Allow mode not yet implemented.")
    
    # Resposta para configuração no modo 'allow'
    # Não vai ser implementada a princípio
    def get_allow_answer(self):
        raise Exception("Allow mode not yet implemented.")
    
    # Esse metodo retorna a string que deve ser enviado ao cliente caso
    # o servidor esteja configurado no modo deny.
    # Nesse modo ele ignora se o cliente pediu ou não para o servidor
    # não atualizar as entradas. Simplismente responde que vai atualizar.
    # O que difere esse modo do modo ignore é que aqui nos respondemos adequadamente ao cliente.
    # O trabalho aqui é setar os bits na resposta de forma apropriada.
    def get_deny_answer(self):
        # Variaveis dos bits que serao enviados na resposta
        n = False
        e = False
        o = False
        s = True
        format_str = "\\%03o\\000\\000%s"
        
        # Compara o que o cliente enviou com o que vamos enviar
        if n != self.dont_update or s != self.server_update_a:
            o = True

        bin_str = ['0', '0', '0', '0']
        if n:
            bin_str[0] = '1'
        if e:
            bin_str[1] = '1'
        if o:
            bin_str[2] = '1'
        if s:
            bin_str[3] = '1'

        # Converte para inteiro
        int_bin = int(''.join(bin_str), 2)
        
        # Retorna a resposta do jeito que o FreeRADIUS espera
        return format_str % (int_bin, self.fqdn)
    
    def __unicode__(self):        
        return "N:%s E:%s O:%s S:%s FQDN:%s" % (self.dont_update, not self.ascii_encoding, \
                                                self.server_override, self.server_update_a, self.fqdn)
        
    def __str__(self):
        return unicode(self).encode('utf-8')