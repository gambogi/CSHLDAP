#!/usr/bin/python
# written for python 2.7

import ldap as pyldap       
import ldap.sasl as sasl
import ldap.modlist
from copy import deepcopy

class CSHLDAP:
    def __init__(self, user, password, host='ldap://ldap.csh.rit.edu', \
            base='ou=Users,dc=csh,dc=rit,dc=edu', bind='ou=Apps,dc=csh,dc=rit,dc=edu', app = False):
        self.host = host
        self.base = base        
        if not app:
            try:
                self.ldap = pyldap.initialize(host)
                auth = sasl.gssapi("")
            	self.ldap.sasl_interactive_bind_s("", auth)
            	self.ldap.set_option(pyldap.OPT_DEBUG_LEVEL,0)
            except pyldap.LDAPError, e:
            	print 'Are you sure you\'ve run kinit?'
            	print e
	else:
            self.ldap = pyldap.initialize(host)
	    self.base = base
            self.ldap.simple_bind('cn='+user+','+bind, password)

    def members(self, uid="*"):
        """ members() issues an ldap query for all users, and returns a dict
            for each matching entry. This can be quite slow, and takes roughly 
            3s to complete. You may optionally restrict the scope by specifying
            a uid, which is roughly equivalent to a search(uid='foo')
        """
        entries = self.ldap.search_s(self.base,pyldap.SCOPE_SUBTREE,'(uid='+uid+')', ['*','+'])
        result = []
        for entry in entries:
            result.append(entry[1])
        return result

    def member(self, user):
        """ Returns a user as a dict of attributes 
        """
        return list(self.ldap.search_s(self.base,pyldap.SCOPE_SUBTREE,'(uid='+user+')', ['*','+'])[0])[1]

    def search( self, **kwargs ):
        filterstr =''
        for key, value in kwargs.iteritems():
            filterstr += '({0}={1})'.format(key,value)

        if len(kwargs) > 1:
            filterstr = '(&'+filterstr+')'
        return self.ldap.search_s(self.base, pyldap.SCOPE_SUBTREE, filterstr, ['*','+'])
    
    def modify( self, uid, **kwargs ):
        dn = 'uid='+uid+',ou=Users,dc=csh,dc=rit,dc=edu'
        old_attrs = self.member(uid)
        new_attrs = deepcopy(old_attrs)

        for field, value in kwargs.iteritems():
            if field in old_attrs:
                new_attrs[field] = [str(value)]
        modlist = pyldap.modlist.modifyModlist(old_attrs, new_attrs)
        
        self.ldap.modify_s(dn, modlist)

class KerberosTicket:
    def __init__(self, service):
        __, krb_context = kerberos.authGSSClientInit(service)
        kerberos.authGSSClientStep(krb_context, "")
        self._krb_context = krb_context
        self.auth_header = ("Negotiate " +
                            kerberos.authGSSClientResponse(krb_context))
    def verify_response(self, auth_header):
        # Handle comma-separated lists of authentication fields
        for field in auth_header.split(","):
            kind, __, details = field.strip().partition(" ")
            if kind.lower() == "negotiate":
                auth_details = details.strip()
                break
        else:
            raise ValueError("Negotiate not found in %s" % auth_header)
        # Finish the Kerberos handshake
        krb_context = self._krb_context
        if krb_context is None:
            raise RuntimeError("Ticket already used for verification")
        self._krb_context = None
        kerberos.authGSSClientStep(krb_context, auth_details)
        kerberos.authGSSClientClean(krb_context)
