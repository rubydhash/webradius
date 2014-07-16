from django.contrib import admin
from webradius.models import Radcheck, Radacct, Radgroupcheck, Radgroupreply, Radippool, Radpostauth, Radreply, Radusergroup, Poolinfo, Nas, Macinfo, Log

admin.site.register(Radcheck)
admin.site.register(Radacct)
admin.site.register(Radgroupcheck)
admin.site.register(Radgroupreply)
admin.site.register(Radippool)
admin.site.register(Radpostauth)
admin.site.register(Radreply)
admin.site.register(Radusergroup)
admin.site.register(Poolinfo)
admin.site.register(Nas)
admin.site.register(Macinfo)
admin.site.register(Log)