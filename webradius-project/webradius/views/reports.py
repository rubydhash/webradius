# -*- coding: utf-8 -*-

from django.views import generic
from django import shortcuts
from django.db.models import Count
from lib.djangoutils  import customviews

from webradius import models

import datetime

class ReportsView(generic.View):
    template_name = 'webradius/reports.html'
    
    def get(self, request, *args, **kwargs):
        return shortcuts.render(request, self.template_name)
    
class ReportsMovedMacsView(customviews.SuperuserResctrictedView):
    template_name = 'webradius/reports_movedmacs.html'
        
    def get(self, request, *args, **kwargs):        
        # Essa query nao esta muito bonita mas foi feita para gerar um relario rapidamente     
        object_list = models.Radippool.objects.raw("""select r.*, m.id as mac_id, m.pool as associated_pool_id, m.static, m.static_ip,
                                                      (select pool_name from poolinfo where id = m.pool) as associated_pool_name,
                                                      (select id from poolinfo where pool_name = r.pool_name) as effective_pool_id
                                                      from radippool as r, macinfo as m
                                                      where r.pool_key = m.mac and
                                                      r.pool_name != (select pool_name from poolinfo where id = m.pool) and
                                                      r.expiry_time > '0001-01-01 00:00:00' and
                                                      r.expiry_time > 'now'::timestamp(0) and r.expiry_time is not null""")

        return shortcuts.render(request, self.template_name, {'object_list': object_list})
    
class ReportsOpenSessionsView(customviews.SuperuserResctrictedView):
    template_name = 'webradius/reports_opensessions.html'
    
    def get(self, request, *args, **kwargs):             
        object_list = models.Radacct.objects.filter(acctstarttime__isnull=False).filter(acctstoptime__isnull=True).order_by('-acctstarttime')

        return shortcuts.render(request, self.template_name, {'object_list': object_list})
    
class ReportsPostAuthView(generic.View):
    template_name = 'webradius/reports_postauth.html'
    
    def __get_key(self, obj):
        return obj.authdate
    
    def get(self, request, *args, **kwargs):
        object_list = models.Radpostauth.objects.exclude(reply='Access-Accept').distinct('username').order_by('username', '-authdate')[:150]

        object_list = sorted(object_list, key=self.__get_key, reverse=True)

        return shortcuts.render(request, self.template_name, {'object_list': object_list})

class ReportsPostAuthSessionsView(generic.View):
    template_name = 'webradius/reports_postauth_sessions.html'

    def get(self, request, *args, **kwargs):
        postauth = shortcuts.get_object_or_404(models.Radpostauth, pk=self.kwargs.get('pk'))

        accts = models.Radacct.objects.filter(nasportid=postauth.nasportid, nasipaddress=postauth.nasipaddress).order_by('-acctstarttime')
        final_accts = []

        for acct in accts:
            if acct.acctstoptime is None:
                stoptime = datetime.datetime(year=9999, month=12, day=31, hour=23, minute=59, second=59)
            else:
                stoptime = acct.acctstoptime

            if not (postauth.authdate >= acct.acctstarttime and postauth.authdate <= stoptime):
                continue
            final_accts.append(acct)

        return shortcuts.render(request, self.template_name, {'object_list': final_accts})
    
class ReportsQtdSessionsView(customviews.SuperuserResctrictedView):
    template_name = 'webradius/reports_qtdsessions.html'
    
    def get(self, request, *args, **kwargs):
        diff = datetime.datetime.now() - datetime.timedelta(days=30)
        object_list = models.Radacct.objects.values('username').filter(acctstarttime__gt=diff).annotate(user_count=Count('username')).order_by('-user_count')[:100]
        
        return shortcuts.render(request, self.template_name, {'object_list': object_list})