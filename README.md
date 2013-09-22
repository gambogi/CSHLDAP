CSHLDAP
=======

CSHLDAP is a python 2.7 library designed to make interfacing with LDAP less painful
for the average CSHer. 

## Installation

CSHLDAP depends on `python-ldap` ([homepage](http://www.python-ldap.org/)).

    $ python --version
     Python 2.7.3
    $ pip install CSHLDAP

(or just download the source)

## Basic Usage
```python
#!/usr/bin/python
from CSHLDAP import CSHLDAP

# Creates a connection to CSH's ldap server as an object with some 
# helper functions
ldap = CSHLDAP('<user>','<password>')
    
# Returns a list of results, in this case of users whose uid starts with
# 'duck'.  All CSH LDAP fields are included in a similar way
ldap.search(uid='duck*')
  
# This will return users whose common names (cn) start with 'Chris'
ldap.search(cn='Chris')

# This will return users whose uid starts with 'user', and cn
# starts with 'Name'
ldap.search(uid='user*', cn='Name*')

# Returns a dict of a user's attributes. Performs a search, and then grabs
# the first result. Are you feelin' lucky?
ldap.member('uidValue')

# Equivalent to search(uid='*')
ldap.members()

# You may optionally include a search string. 
# Equivalent to search(uid='username')
ldap.members('test')
```

## Functions

### search()

Search returns a list of tuples containing a string and a dictionary. 
The first element of each tuple is the Distinguished Name (dn) of the entry.
This is the path to the entry in ldap. The second element of each tuple is a
dictionary of attributes as keys. 

So to be clear the return looks like this: `[('dn',{attributes})]`

####WARNING: Not all users have the same attribute fields in their dictionary
Do not depend on all users having a `twitterName` for example.


## Rationale

### Why is search()'s implementation so ugly?
If you have looked at the source, you may be ready to throw something at me. 
I would like to stress that this is a library intended for people who wouldn't
touch ldap with a 10ft pole. The decision to have that optional field vomit was
made so that writing easy to read lines like `search(active=1)` are possible.
If you desire more functionality I encourage you to write your own ldap queries 
with [python-ldap](http://www.python-ldap.org/), it's not that bad.

Or make a pull request.

### Why not python3? 
Simple. `python3-ldap` is currently in beta. `python-ldap` currently works. A 
python3 version will be written, but for now I'm sticking with the supported 
module.
