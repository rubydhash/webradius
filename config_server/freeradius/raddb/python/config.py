# -*- coding: utf-8 -*-
#
# Arquivo com variáveis de configuração

# Variaveis de configuração do modulo
db_hostname = '192.168.1.2'
db = 'bd_radius'
db_user_name = 'radius'
db_passwd = 'password-example'
db_port = 5432

dns_server_ip = '192.168.1.1'
dns_key_name = 'dns-key-example'
dns_key = 'dns-key-pass-example'
dns_ttl = 24 * 60 * 60

# Modo de funcionamento, por enquanto só foi implementado o 'deny'
# Os outros modos seriam 'ignore' e 'allow'
# Segue a descrição de cada modo:
#  * Ignore: Ignora qualquer informação que o cliente tenha enviado no FQDN e força
#            que o servidor atualize o DNS.
#  * Deny: Testa as flags do FQDN enviadas pelo cliente e responde de modo a indicar ao cliente
#          que o servidor é que vai atualizar o DNS.
#          O que difere esse modo do modo ignore é que aqui nos respondemos adequadamente ao cliente.
#  * Allow: Se o cliente pedir para ele mesmo atualizar o DNS o servidor vai respeitar isso
#           indicando esse comportamente através dos bits do FQDN.
mode = "deny"

# Opções do pool de conexões
min_conn = 10
max_conn = 10

# Uma semana para retirar as entradas DNS
rotateseconds = 7 * 24 * 60 * 60