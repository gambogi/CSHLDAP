#!/usr/bin/python
# written for python 2.7

import ldap as pyldap       
import ldap.sasl as sasl

class CSHLDAP:
    def __init__(self, user, password, host='ldap://ldap.csh.rit.edu', \
            base='ou=Users,dc=csh,dc=rit,dc=edu', bind='ou=Apps,dc=csh,dc=rit,dc=edu'):
        self.host = host
        self.base = base        
        
        try:
            self.ldap = pyldap.initialize(host)
            auth = sasl.gssapi("")
            self.ldap.sasl_interactive_bind_s("", auth)
            self.ldap.set_option(pyldap.OPT_DEBUG_LEVEL,0)
        except pyldap.LDAPError, e:
            print e

        #self.ldap.simple_bind('cn='+user+','+bind, password


    def members(self, uid="*"):
        """ members() issues an ldap query for all users, and returns a dict
            for each matching entry. This can be quite slow, and takes roughly 
            3s to complete. You may optionally restrict the scope by specifying
            a uid, which is roughly equivalent to a search(uid='foo')
        """
        entries = self.ldap.search_s(self.base,pyldap.SCOPE_SUBTREE,'(uid='+uid+')')
        result = []
        for entry in entries:
            result.append(entry[1])
        return result

    def member(self, user):
        """ Returns a user as a dict of attributes 
        """
        return list(self.ldap.search_s(self.base,pyldap.SCOPE_SUBTREE,'(uid='+user+')')[0])[1]

    def search( self, **kwargs):
        filterstr =''
        for key, value in kwargs.iteritems():
            filterstr += '({0}={1})'.format(key,value)

        if len(kwargs) > 1:
            filterstr = '(&'+filterstr+')'
        return self.ldap.search_s(self.base, pyldap.SCOPE_SUBTREE, filterstr)


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
