# -*- coding: utf-8 -*-
# Generate and upload personal dictionary to Linksys SPA 921/922 
import ldap3,wget,re,socket,sys,os,requests,time,urllib2

##################################
ad_user = 'host'
ad_pass = 'user'
ad_host = 'pass'
ad_basedn = 'DC=host,DC=example,DC=com'
ad_attr = ['sAMAccountName','name','telephoneNumber']
##################################
# Check host exists
def check_host(hostname):
    try:
        socket.gethostbyname(hostname)
        return 1    # OK
    except socket.error:
        return 0    # Error

# Check host alive
def check_host_alive(hostname):
    try:
        urllib2.urlopen(hostname, timeout=1)
        return 1    # OK
    except urllib2.URLError as err:
        return 0    # Error
print "Starting ..."
print "-"*45
# AD connect
ad_connect = ldap3.Connection(server=ad_host,user=ad_user,password=ad_pass,version=3,authentication='SIMPLE')
if not ad_connect.bind():
    print ("ERROR: not connect to AD server"); sys.exit()
else:
    print "=> Connect to "+ad_host+ " is success."

# Get data from AD, generate contacts list and URL list
total_entries = 0
ad_connect.search(search_base=ad_basedn,search_filter='(objectclass=person)',attributes=ad_attr)
total_entries += len(ad_connect.response)
if total_entries > 0:
    contacts_list = []
    url_list = []
    total_contacts = 0
    for entry in ad_connect.response:
        if entry['attributes']['telephoneNumber']:
            name = entry['attributes']['name']
            account = (entry['attributes']['sAMAccountName']).replace('.','_')
            phone_number = entry['attributes']['telephoneNumber']
            contacts_list.append("n="+name+";p="+phone_number+";r=10") # example: Vasya Pupkin;p=251;r=10
            url_list.append("sip-"+account) # example: sip-pupkin
            total_contacts +=1
ad_connect.unbind()
print "=> Found "+str(total_contacts)+" contacts."
if len(url_list) > 0:
    print "=> Checking host exist ..."
    for host in url_list:
        if check_host(host) == 0:
            print "=> ERROR: host "+host+" not found. Continue ..."
            pass
        else:
            url = "http://"+host+"/"
            if check_host_alive(url) == 0:
                print "=> ERROR: host "+host+" is DOWN. Continue ..."
            else:
                print "=> Download pdir.htm from: "+url
                url_file = wget.download(url+"pdir.htm")
                print "=> Generate contact list for host "+host
                file_open = open(url_file, 'r')
                number_list = []
                empty_list = {}
                for line in file_open:
                    if re.search('^<tr ', line):
                        line = line.split('name=')
                        list_number_1 = line[1].split(' ')[0].replace('"', '')
                        number_list.append(list_number_1)
                        list_number_2 = line[2].split(' ')[0].replace('"', '')
                        number_list.append(list_number_2)
                file_open.close()
                os.unlink('pdir.htm')
                # Generate new contact list
                data = (zip(number_list, contacts_list+[None]*(len(number_list) - len(contacts_list))))
                new_contact_list = dict((x, y) for x, y in data)
                # Generate empty list
                for n in number_list:
                    empty_list[n] = '='
                # First upload empty contact list to IPPhone
                print "=> Upload empty contacts list to: "+host+" ..."
                requests.post(url+"pdir.spa", data=empty_list)
                # Upload new contact list to IPPhone
                time.sleep(10)
                print "=> Upload new contacts list to: " + host + " ..."
                requests.post(url+"pdir.spa", data=new_contact_list)
                time.sleep(2)
                print "=> The contact list was successfully uploaded for host: "+host+"."
else:
    print "=> Exit"
    sys.exit()
print "-"*45
print "Finishing"
