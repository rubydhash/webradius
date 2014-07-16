import os, os.path, sys
sys.path.append('/usr/local/lib/webradius-project')
sys.stdout = sys.stderr
#os.environ['DJANGO_SETTINGS_MODULE'] = 'webradius-project.settings'
os.environ['DJANGO_SETTINGS_MODULE'] = 'webradius-project.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
