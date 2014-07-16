# -*- coding: utf-8 -*-

from django.views import generic
from django import shortcuts
from webradius import models

class IndexView(generic.View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return shortcuts.render(request, 'webradius/home.html', 
                                    {'lastchange': models.Log.objects.all().order_by('-created')[:10]})
        else:
            return shortcuts.render(request, 'webradius/home.html', 
                                    {'lastchange': models.Log.objects.filter(user=request.user).order_by('-created')[:10]})