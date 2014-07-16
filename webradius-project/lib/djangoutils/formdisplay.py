# -*- coding: utf-8 -*-

from django.db import models
from django import forms

from django.utils.html import conditional_escape
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django.core.exceptions import ValidationError
from django.forms.fields import Field, FileField
from django.forms.util import flatatt, ErrorDict, ErrorList
from django.forms.widgets import Media, media_property, TextInput, Textarea
from django.utils.datastructures import SortedDict
from django.utils.encoding import StrAndUnicode, smart_unicode, force_unicode
from django.utils.safestring import mark_safe


class CustomErrorDict(ErrorDict):
    def as_ul(self):
        if not self: return u''
        msgform = _(u'Por favor, corrija os erros abaixo.')
        return mark_safe(u'<div class="alert alert-error"> <h4>%s</h4> <ul class="errorlist">%s</ul></div>'
                % (msgform,''.join([u'<li class="erroritem"><span class="erroritemlabel">%s</span> <span class="erroritemdesc">%s</span></li>' % (v[0], conditional_escape(force_unicode(v[1])))
                    for k, v in self.items()])))

        
class CustomErrorList(ErrorList):
    def as_ul(self):
        if not self: return u''
        return mark_safe(u'%s &nbsp;'
                % ''.join([u'%s' % conditional_escape(force_unicode(e)) for e in self]))


class CustomBaseForm(forms.BaseForm):
    def as_p(self):
        "Returns this form rendered as HTML <p>s."
        return self._html_output(
            normal_row = u'<p%(html_class_attr)s>%(label)s %(field)s%(help_text)s</p>',
            error_row = u'%s',
            row_ender = '</p>',
            help_text_html = u' <br/><span class="helptext">%s</span>',
            errors_on_separate_row = False)
            

        
class CustomBaseForm2(forms.BaseForm):
    def __init__(self,*args,**kwargs):
        super(CustomBaseForm,self).__init__(*args, **kwargs)
        self.error_class = CustomErrorList
        
    def as_p(self):
        "Returns this form rendered as HTML <p>s."
        return self._html_output(
            normal_row = u'<p%(html_class_attr)s>%(label)s %(field)s%(help_text)s</p>',
            error_row = u'%s',
            row_ender = '</p>',
            help_text_html = u' <br/><span class="helptext">%s</span>',
            errors_on_separate_row = False)

    def full_clean(self):
        """
        Cleans all of self.data and populates self._errors and
        self.cleaned_data.
        """
        self._errors = CustomErrorDict()
        if not self.is_bound: # Stop further processing.
            return
        self.cleaned_data = {}
        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return
        self._clean_fields()
        self._clean_form()
        self._post_clean()
        if self._errors:
            del self.cleaned_data
            
    def _clean_fields(self):
        for name, field in self.fields.items():
            # value_from_datadict() gets the data from the data dictionaries.
            # Each widget type knows how to retrieve its own data, because some
            # widgets split data over several HTML fields.
            value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, FileField):
                    initial = self.initial.get(name, field.initial)
                    value = field.clean(value, initial)
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except ValidationError, e:
                self._errors[name] = (field.label,self.error_class(e.messages)) # Display Label e Messages
                if name in self.cleaned_data:
                    del self.cleaned_data[name]
                    
                   
