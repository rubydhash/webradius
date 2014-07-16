# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Andrey Antukh <niwi@niwi.be>
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json

from django import forms
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import six
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _


TYPES = {
    'int': int,
    'smallint': int,
    'text': str,
    'double precision': float,
    'varchar': str,
    'inet': str,
}

def _cast_to_unicode(data):
    if isinstance(data, (list, tuple)):
        return [_cast_to_unicode(x) for x in data]
    elif isinstance(data, str):
        return force_text(data)
    return data


def _cast_to_type(data, type_cast):
    if isinstance(data, (list, tuple)):
        return [_cast_to_type(x, type_cast) for x in data]
    if type_cast == str:
        return force_text(data)
    return type_cast(data)


def _unserialize(value):
    if not isinstance(value, six.string_types):
        return _cast_to_unicode(value)

    try:
        return _cast_to_unicode(json.loads(value))
    except ValueError:
        return _cast_to_unicode(value)


class ArrayField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self._array_type = kwargs.pop('dbtype', 'int')
        type_key = self._array_type.split('(')[0]

        try:
            self._type_cast = TYPES[type_key]
        except KeyError:
            raise TypeError('invalid postgreSQL type: %s' % self._array_type)

        self._dimension = kwargs.pop('dimension', 1)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('null', True)
        kwargs.setdefault('default', None)
        super(ArrayField, self).__init__(*args, **kwargs)

    def formfield(self, **params):
        params.setdefault('form_class', ArrayFormField)
        return super(ArrayField, self).formfield(**params)

    def db_type(self, connection):
        return '{0}{1}'.format(self._array_type, "[]" * self._dimension)

    def get_db_prep_value(self, value, connection, prepared=False):
        value = value if prepared else self.get_prep_value(value)
        if not value or isinstance(value, six.string_types):
            return value
        return _cast_to_type(value, self._type_cast)

    def get_prep_value(self, value):
        if value is not None:
            return '{%s}' % ','.join(value)
        else:
            return '{}'

    def to_python(self, value):
        return _unserialize(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return json.dumps(self.get_prep_value(value),
                          cls=DjangoJSONEncoder)

    def validate(self, value, model_instance):
        for val in value:
            super(ArrayField, self).validate(val, model_instance)

class ArrayFormField(forms.Field):
    default_error_messages = {
        'invalid': _('Enter a list of values, joined by commas. E.g. "a,b,c".'),
    }

    def __init__(
            self, max_length=None, min_length=None, delim=None,
            *args, **kwargs):
        if delim is not None:
            self.delim = delim
        else:
            self.delim = ','
        super(ArrayFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            return []
        # If Django already parsed value to list
        if isinstance(value, list):
            return value
        try:
            return value.split(self.delim)
        except Exception:
            raise ValidationError(self.error_messages['invalid'])

    def prepare_value(self, value):
        if value:
            v = value
        else:
            v = super(ArrayFormField, self).prepare_value(value)
        if v is not None:
            if isinstance(v, dict):
                return ""
            else:                
                return v.replace('{','').replace('}','')
        else:
            return v

    def to_python(self, value):
        return value.split(self.delim)
    