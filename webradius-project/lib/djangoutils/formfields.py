# -*- coding: utf-8 -*-

from django.forms.widgets import Select
from django.utils.html import escape, conditional_escape
from django import forms
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.core.urlresolvers import reverse
from django.forms.util import  ValidationError
import unicodedata

class StrippedCharField(forms.CharField):
    def __init__(self, max_length=None, min_length=None, strip=True, lower=False, upper=False, normalize=False, *args, **kwargs):
        super(StrippedCharField, self).__init__(max_length, min_length, *args, **kwargs)
        self.strip = strip
        self.lower = lower
        self.upper = upper
        self.normalize = normalize

    def clean(self, value):
        if self.strip and value:
            value = value.strip()
            if self.lower:
                value = value.lower()
            if self.upper:
                value = value.upper()
            if self.normalize:
                value = unicodedata.normalize('NFKD', unicode(value)).encode('ASCII','ignore')
        return super(StrippedCharField, self).clean(value)
        

class SelectWithDisabled(Select):
    """
    Subclass of Django's select widget that allows disabling options.
    To disable an option, pass a dict instead of a string for its label,
    of the form: {'label': 'option label', 'disabled': True}
    """
    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        if (option_value in selected_choices):
            selected_html = u' selected="selected"'
        else:
            selected_html = ''
        disabled_html = ''
        if isinstance(option_label, dict):
            if dict.get(option_label, 'disabled'):
                disabled_html = u' disabled="disabled"'
            option_label = option_label['label']
        return u'<option value="%s"%s%s>%s</option>' % (
            escape(option_value), selected_html, disabled_html,
            conditional_escape(force_unicode(option_label)))
        
#Autocomplete
CLIENT_CODE = """
<input type="text" name="%s" id="%s" value="%s"/> <span id="autocomplete_label_%s" class="autocomplete_label"><span>

<script type="text/javascript">

    $(function() {
        $( "#%s" ).autocomplete({
            source: "%s",
            minLength: 2,
            select: function( event, ui ) {
                $("#autocomplete_label_%s").html(ui.item.label);
            }
        });
    });

</script>
"""

class ModelAutoCompleteWidget(forms.widgets.TextInput):
    """ widget autocomplete for text fields
    """
    html_id = ''
    def __init__(self,lookup_url=None,*args, **kw):
        super(forms.widgets.TextInput, self).__init__(*args, **kw)
        self.lookup_url = lookup_url

    def render(self, name, value, attrs=None):
        if value == None:
            value = ''
        html_id = attrs.get('id', name)
        self.html_id = html_id

        lookup_url = self.lookup_url
        detail_url = None


        return mark_safe(CLIENT_CODE %(name, html_id, value,html_id,html_id,lookup_url,html_id))


    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, returns the value
        of this widget. Returns None if it's not provided.
        """

        return data.get(name, None)




class ModelAutoCompleteField(forms.fields.CharField):
    """
    Autocomplete form field for Model Model
    """
    model = None
    url = None

    def __init__(self, model,  lookup_url, *args, **kwargs):
        self.model,self.url = model,lookup_url,
        super(ModelAutoCompleteField, self).__init__(
            widget = ModelAutoCompleteWidget(lookup_url=self.url),
            max_length=255,
            *args, **kwargs)


    def clean(self, value):
        try:
            obj = self.model.objects.get(pk=value)
        except:
            raise ValidationError(u'Valor inválido')
        return obj
