# -*- coding: utf-8 -*-

import datetime

class DateTimeUtils:
    # Devido a bugs do strptime com threads, http://bugs.python.org/issue7980, foi
    # implementada essa função que faz o parsing de datas no seguinte formato:
    # '%d-%m-%Y %H:%M:%S'
    # '02-09-2013 18:36:23'
    @classmethod
    def mystrptime(cls, str_date):
        d, m, y, h, mi, s = str_date.replace('-', ' ').replace(':', ' ').split()
        return datetime.datetime(int(y), int(m), int(d), int(h), int(mi), int(s))