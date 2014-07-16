import ldap
from django.conf import settings
from django.contrib.auth.models import User, check_password

class LdapBackend:
    """Authenticate using LDAP
    """
    def authenticate(self, username=None, password=None):
        l = ldap.open(settings.LDAP_AUTH_SERVER, settings.LDAP_AUTH_PORT)
        userdn = settings.LDAP_AUTH_USERDN % username       
        try:
            l.simple_bind_s(userdn, password)
            valid = True
        except ldap.LDAPError, e:
            valid = False

        if valid:
            
            searchScope = ldap.SCOPE_SUBTREE
            retrieveAttributes = None 
            searchFilter = "uid=%s" %username
            LDAP_AUTH_user_info = {}
            
            try: 
                LDAP_AUTH_result_id = l.search(settings.LDAP_AUTH_BASEDN, searchScope, searchFilter, retrieveAttributes)
                result_type, result_data = l.result(LDAP_AUTH_result_id, 0)
                LDAP_AUTH_user_info['cn'] = result_data[0][1].get('cn')[0]
            except: 
                pass

                
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. Note that we can set password to anything
                # as it won't be checked, the password from settings.py will.
                user = User(username=username)
                if LDAP_AUTH_user_info.get('cn'):
                    user.first_name=LDAP_AUTH_user_info.get('cn')
                user.is_staff = True
                user.is_superuser = False
                user.set_unusable_password()
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
    def get_user_by_name(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None