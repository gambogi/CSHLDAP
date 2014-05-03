#!/usr/bin/python
# written for python 2.7, tested on 2.6

import ldap as pyldap
import ldap.sasl as sasl
import ldap.modlist
import re
from datetime import datetime, date
from copy import deepcopy

class CSHLDAP:
    def __init__(self, user, password, host='ldaps://ldap.csh.rit.edu:636', \
            base='ou=Users,dc=csh,dc=rit,dc=edu', bind='ou=Apps,dc=csh,dc=rit,dc=edu', app = False):
        self.host = host
        self.base = base
        self.users = 'ou=Users,dc=csh,dc=rit,dc=edu'
        self.groups = 'ou=Groups,dc=csh,dc=rit,dc=edu'
        self.committees = 'ou=Committees,dc=csh,dc=rit,dc=edu'
        self.ldap = pyldap.initialize(host)
        self.ldap.set_option(pyldap.OPT_X_TLS_DEMAND, True)
        self.ldap.set_option(pyldap.OPT_DEBUG_LEVEL, 255)

        if app:
            self.ldap.simple_bind('uid=' + user + ',' + base, password)
            # self.ldap.simple_bind('uid='+user+','+bind, password)
        else:
            try:
                auth = sasl.gssapi("")

                self.ldap.sasl_interactive_bind_s("", auth)
            	self.ldap.set_option(pyldap.OPT_DEBUG_LEVEL,0)
            except pyldap.LDAPError, e:
            	print 'Are you sure you\'ve run kinit?'
            	print e

    def members(self, uid="*", objects=False):
        """ members() issues an ldap query for all users, and returns a dict
            for each matching entry. This can be quite slow, and takes roughly
            3s to complete. You may optionally restrict the scope by specifying
            a uid, which is roughly equivalent to a search(uid='foo')
        """
        entries = self.search(uid='*')
        if objects:
            return self.memberObjects(entries)
        result = []
        for entry in entries:
            result.append(entry[1])
        return result

    def member(self, user, objects=False):
        """ Returns a user as a dict of attributes
        """
        try:
            member = self.search(uid=user, objects=objects)[0]
        except IndexError:
            return None
        if objects:
            return member
        return member[1]

    def eboard(self, objects=False):
        """ Returns a list of eboard members formatted as a search
            inserts an extra ['commmittee'] attribute
        """
        # self.committee used as base because that's where eboard
        # info is kept
        committees = self.search(base = self.committees, cn='*')
        directors = []
        for committee in committees:
            for head in committee[1]['head']:
                director = self.search(dn=head)[0]
                director[1]['committee'] = committee[1]['cn'][0]
                directors.append(director)
        if objects:
            return self.memberObjects(directors)
        return directors

    def group(self, group_cn, objects=False):
        members = self.search(base=self.groups,cn=group_cn)
        if len(members) == 0:
            return members
        else:
            member_dns = members[0][1]['member']
        members = []
        for member_dn in member_dns:
            members.append(self.search(dn=member_dn)[0])
        if objects:
            return self.memberObjects(members)
        return members

    def getGroups(self, member_dn):
        searchResult = self.search(base=self.groups, member=member_dn)
        if len(searchResult) == 0: return []

        groupList = []
        for group in searchResult:
            groupList.append(group[1]['cn'][0])
        return groupList

    def drinkAdmins(self, objects=False):
        """ Returns a list of drink admins uids
        """
        admins = self.group('drink', objects=objects)
        return admins

    def rtps(self, objects=False):
        rtps = self.group('rtp', objects=objects)
        return rtps

    def trimResult(self, result):
        return [x[1] for x in result]

    def search( self, base=False, trim=False, objects=False, **kwargs ):
        """ Returns matching entries for search in ldap
            structured as [(dn, {attributes})]
            UNLESS searching by dn, in which case the first match
            is returned
        """
        scope = pyldap.SCOPE_SUBTREE
        if not base:
            base = self.users

        filterstr =''
        for key, value in kwargs.iteritems():
            filterstr += '({0}={1})'.format(key,value)
            if key == 'dn':
                filterstr = '(objectClass=*)'
                base = value
                scope = pyldap.SCOPE_BASE
                break

        if len(kwargs) > 1:
            filterstr = '(&'+filterstr+')'

        result = self.ldap.search_s(base, pyldap.SCOPE_SUBTREE, filterstr, ['*','+'])
        if base == self.users:
            for member in result:
                groups = self.getGroups(member[0])
                member[1]['groups'] = groups
                if 'eboard' in member[1]['groups']:
                    member[1]['committee'] = self.search(base=self.committees, \
                           head=member[0])[0][1]['cn'][0]
        if objects:
            return self.memberObjects(result)
        finalResult = self.trimResult(result) if trim else result
        return finalResult

    def modify( self, uid, base=False, **kwargs ):
        if not base:
            base = self.users
        dn = 'uid='+uid+',ou=Users,dc=csh,dc=rit,dc=edu'
        old_attrs = self.member(uid)
        new_attrs = deepcopy(old_attrs)

        for field, value in kwargs.iteritems():
            if field in old_attrs:
                new_attrs[field] = [str(value)]
        modlist = pyldap.modlist.modifyModlist(old_attrs, new_attrs)

        self.ldap.modify_s(dn, modlist)

    def memberObjects( self, searchResults ):
        results = []
        for result in searchResults:
            newMember = Member(result, ldap=self)
            results.append(newMember)
        return results

class Member(object):
    def __init__(self, member, ldap=None):
        """ Creates and returns a member object from which LDAP fields
            are accessible as properties. If you supply an LDAP connection,
            the object will use that connection to reload its data and
            modify its fields if you choose.
        """
        self.specialFields = ("memberDict", "ldap")
        if len(member) < 2:
            self.memberDict = {}
        else:
            self.memberDict = member[1]
        self.ldap = ldap

    def __getattr__(self, attribute):
        """ Accesses the internal dictionary representation of
            a member and returns whatever data type it represents.
        """
        if (attribute == "specialFields" or
            attribute in self.specialFields):
            return object.__getattribute__(self, attribute)
        try:
            # Grab the object at that key. It will be a list,
            # if it exists.
            attributes = self.memberDict[attribute]

            # If we do get a list, and it only
            # contains one thing, just return that
            # one thing.
            if len(attributes) == 1:
                attribute = attributes[0]
                # If it's a digit, convert it to an int and return.
                if attribute.isdigit():
                    attribute = int(attribute)
                # Return the attribute.
                return attribute
            # Return the list.
            return attributes
        # If there was an error (i.e. that member doesn't have that
        # key in their LDAP store), then return None. We couldn't get it.
        except (KeyError, IndexError):
            return None

    def __setattr__(self, attribute, value):
        """ When setting an attribute with 'member.field = "value"',
            access the internal ldap connection from the constructor
            and modify that parameter.
        """
        if (attribute == "specialFields" or
            attribute in self.specialFields):
            return object.__setattr__(self, attribute, value)
        if attribute in ("memberDict", "ldap"):
            object.__setattr__(self, attribute, value)
            return
        if not self.ldap:
            return
        kwargs = {attribute : value}
        self.ldap.modify(uid=self.uid, **kwargs)
        self.memberDict[attribute] = value

    def fields(self):
        """ Returns all of the keys in the internal dictionary.
        """
        return self.memberDict.keys()

    def isActive(self):
        """ Is the user active?
        """
        return bool(self.active)

    def isAlumni(self):
        """ Is the user an alumnus/a?
        """
        return bool(self.alumni)

    def isDrinkAdmin(self):
        """ Is the user a drink admin?
        """
        return bool(self.drinkAdmin)

    def isOnFloor(self):
        """ Is the user on floor?
        """
        return bool(self.onfloor)

    def isEboard(self):
        """ Is the user on Eboard?
        """
        return 'eboard' in self.groups

    def isRTP(self):
        """ Is the user an RTP?
        """
        return 'rtp' in self.groups

    def isBirthday(self):
        """ Is it the user's birthday today?
        """
        if not self.birthday:
            return False
        birthday = self.birthdate()
        today = date.today()
        return (birthday.month == today.month and
                birthday.day == today.day)

    def birthdate(self):
        """ Converts the user's birthday (if it exists) to a datetime.date
            object that can easily be compared with other dates.
        """
        if not self.birthday:
            return None
        return dateFromLDAPTimestamp(self.birthday)

    def joindate(self):
        """ Converts the user's join date (if it exists) to a datetime.date
            object that can easily be compared with other dates.
        """
        if not self.memberSince:
            return None
        joined = self.memberSince
        return dateFromLDAPTimestamp(joined)

    def age(self):
        """ Returns the user's age, determined by their birthdate()
        """
        if not self.birthdate():
            return -1
        adjuster = 0
        today = date.today()
        birthday = self.birthdate()
        if today.month == birthday.month:
            if today.day < birthday.day:
                adjuster -= 1
        elif today.month < birthday.month:
            adjuster -= 1
        return (today.year - birthday.year) + adjuster

    def reload(self):
        """ If there is an LDAP connection, query it for another
            instance of this member and set its internal dictionary
            to that result.
        """
        if not self.ldap:
            return
        self.memberDict = self.ldap.member(self.uid)

    def fullName(self):
        """ Returns a reliable full name (firstName lastName) for every
            member (as of the writing of this comment.)
        """
        if self.givenName and self.sn:
            return "{0} {1}".format(self.givenName, self.sn)
        if self.givenName:
            return self.givenName
        if self.sn:
            return self.sn
        return self.uid

    def __str__(self):
        """ Constructs a string representation of this person, containing
            every key and value in their internal dictionary.
        """
        string = ""
        for key in self.memberDict.keys():
            thing = self.__getattr__(key)
            string += str(key) + ": " + str(thing) + "\n"
        return string

def dateFromLDAPTimestamp(timestamp):
    """ Takes an LDAP date (In the form YYYYmmdd
        with whatever is after that) and returns a
        datetime.date object.
    """
    # only check the first 8 characters: YYYYmmdd
    numberOfCharacters = len("YYYYmmdd")
    timestamp = timestamp[:numberOfCharacters]
    try:
        day = datetime.strptime(timestamp, '%Y%m%d')
        return date(year=day.year, month=day.month, day=day.day)
    except:
        print(timestamp)
