#!/usr/bin/python
import ldap as pyldap       

class CSHLDAP:
    def __init__(self, user, password):
        self.ldap = pyldap.initialize('ldap://ldap.csh.rit.edu')
        self.base = 'ou=Users,dc=csh,dc=rit,dc=edu'
        self.ldap.simple_bind('cn='+user+',ou=Apps,dc=csh,dc=rit,dc=edu',password)

    def members(self):
        """ members() issues an ldap query for all users, and returns a dict
            for each matching entry. This can be quite slow, and takes roughly 
            3s to complete.
        """
        entries = self.ldap.search_s(ldap.base,pyldap.SCOPE_SUBTREE,'(cn=*)')
        result = []
        for entry in entries:
            result.append(entry[1])
        return result

    def member(self, user):
        """ Returns a user as a dict of attributes 
        """
        return list(self.ldap.search_s(ldap.base,pyldap.SCOPE_SUBTREE,'(uid='+user+')')[0])[1]

    def search( self, \
                uid             ='*', \
                memberSince     ='*', \
                objectClass     ='*', \
                uidNumber       ='*', \
                cn              ='*', \
                aolScreenName   ='*', \
                drinkAdmin      ='*', \
                onfloor         ='*', \
                mail            ='*', \
                description     ='*', \
                loginShell      ='*', \
                blogURL         ='*', \
                gidNumber       ='*', \
                birthday        ='*', \
                active          ='*', \
                nickname        ='*', \
                homePhone       ='*', \
                displayName     ='*', \
                mobile          ='*', \
                houseMember     ='*', \
                alumni          ='*', \
                ritYear         ='*', \
                gecos           ='*', \
                sn              ='*', \
                ritDn           ='*', \
                homeDirectory   ='*', \
                ou              ='*', \
                givenName       ='*' ):
        pass;



ldap = CSHLDAP("pval","pvaldb")

members = ldap.members()

print dir(ldap.search(mobile='703'))

for key in members.iterkeys():
    print key

#for member in members:
#    print member['uid']

