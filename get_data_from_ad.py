# -*- coding: utf-8 -*-
##
## Get data from windows active directory
##
import ldap3,re,sys,time

##################################
ad_user = ''
ad_pass = ''
ad_host = ''
ad_basedn = 'DC=host,DC=example,DC=com'
# Here you need to specify the list of attributes
ad_attr = ['sAMAccountName','name','telephoneNumber','mail','memberOf']
##################################

# AD connect
ad_connect = ldap3.Connection(server=ad_host,user=ad_user,password=ad_pass,version=3,authentication='SIMPLE')
if not ad_connect.bind():
    print ("ERROR: not connect to AD server"); sys.exit()
else:
    print "=> Connect to "+ad_host+ " is success."

# Get data from AD
total_entries = 0
ad_connect.search(search_base=ad_basedn,search_filter='(objectclass=person)',attributes=ad_attr)
total_entries += len(ad_connect.response)
if total_entries > 0:
    for entry in ad_connect.response:
        print '-'*20
        for attr in ad_attr:
            if entry['attributes'][attr]:
                attributes = entry['attributes'][attr]
                if type(entry['attributes'][attr]) is list:
                    attributes = ''
                    for list_attr in entry['attributes'][attr]:
                        attributes += list_attr

                print "Attribute \""+str(attr)+"\": "+attributes
            else:
                pass
ad_connect.unbind()

