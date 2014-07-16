# -*- coding: utf-8 -*-

from django.core import exceptions
from django.conf import settings
from django.db.models import fields

class BigAutoField(fields.AutoField):        
    def db_type(self, connection=None):
        for item in settings.DATABASES:
            if settings.DATABASES[item]['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
                return "bigserial"
            else:
                raise NotImplemented
    
    def get_internal_type(self):
        return "BigAutoField"
    
    def to_python(self, value):
        if value is None:
            return value
        try:
            return long(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                _("This value must be a long integer."))