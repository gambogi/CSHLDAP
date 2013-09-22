#!/usr/bin/python
from CSHLDAP import *
import ldap as pyldap

# CHANGE VALUES AS APPROPRIATE 
username = ''
password = ''
ldap = CSHLDAP(username, password)

def testConnection():
    print 'Connecting...'
    iam = ldap.ldap.whoami_s()
    
    if len(iam) == 0:
        print 'Failed to connect. Check your credentials.'
    else:
        print '[PASS]'

def paramSearch():
    print 'Testing single parameter search...'
    try:
        result = ldap.search(uid='gambogi')
        if result[0][0] == 'uid=gambogi,ou=Users,dc=csh,dc=rit,dc=edu':
            print '[PASS]'
        else:
            return '[FAIL]'
    except pyldap.NO_SUCH_OBJECT:
         print '[FAIL] \nAre your sure you have the right credentials?'

def multiParamSearch():
    print 'Testing multiple parameter search...'
    try:
        result = ldap.search(uid='duck*', cn='Emily*')
        if result[0][0] == 'uid=ducktape,ou=Users,dc=csh,dc=rit,dc=edu':
            print '[PASS]'
        else:
            print '[FAIL]'
    except pyldap.NO_SUCH_OBJECT:
        print '[FAIL] \nAre your sure you have the right credentials?'
if username == '' or password == '':
    print 'Username/Password not changed from default, bailing out'
else:
    testConnection()
    paramSearch()
    multiParamSearch()
