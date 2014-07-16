# -*- coding: utf-8 -*-

from django import forms
from webradius import models
from django.utils.translation import ugettext as _

class NASSearchForm(forms.Form):
    shortname = forms.CharField(label=_(u'Nome curto'), min_length=3, max_length=32, required=False)
    nasname = forms.CharField(label=_(u'DNS ou IP'), min_length=3, max_length=128, required=False)
    description = forms.CharField(label=_(u'Descrição'), min_length=3, max_length=200, required=False)
    type = forms.CharField(label=_(u'Tipo'), min_length=3, max_length=30, required=False)
    
class NASAddForm(forms.ModelForm):    
    shortname = forms.CharField(label=_(u'Nome curto'), min_length=3, max_length=32, required=True)
    nasname = forms.CharField(label=_(u'DNS ou IP'), min_length=3, max_length=128, required=True)
    description = forms.CharField(label=_(u'Descrição'), min_length=3, max_length=200, required=True)
    type = forms.CharField(label=_(u'Tipo'), min_length=3, max_length=30, required=True)
    secret = forms.CharField(label=_(u'Senha'), min_length=3, max_length=60, widget=forms.PasswordInput, required=True)

    class Meta:
        model = models.Nas
        fields = ['shortname', 'nasname', 'description', 'type', 'secret']
        
class NASEditForm(NASAddForm):
    def __init__(self, *args, **kwargs):
        super(NASAddForm, self).__init__(*args, **kwargs)
        # Retira o campo que não pode ser editado
        self.fields.pop('shortname')