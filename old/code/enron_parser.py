"""
enron_parser.py

Parses the Enron email corpus available from https://www.cs.cmu.edu/~./enron/

Functions:

get_email_addresses()               : returns a dictionary of sender email address occurance counts and the list of reciepient emails in the corpus

get_links()                                 : (requires a file "addresses.txt" with a single email address on each line) 
                                                    returns a list of emails and a list of links.  Links are represented as a 
                                                    triple (sender, reciepient, datetime object)

createNetworks(addresses,links): input addresses and links from get_links function
                                                    creates files "week$STARTDATE$.pairs" where "$STARTDATE$" is the week start date
                                                    
    Copyright (C) 2014 Leto Peel

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
import os
from sys import stdout
from dateutil.parser import parse
from numpy import argsort
from datetime import timedelta


startdate=parse("Mon, 10 May 1999 00:00:00 +0000 (UTC)")
weekdelta=timedelta(days=7)

def createNetworks(addresses,links):
    weekstart=startdate
    weekNetwork=[]
    #map emails to ids  ----TODO: create names.lut file
    email_ID_dict=dict((k,v) for v,k in enumerate(addresses))
    for link in links:
        #if link occurs after current week, write to file and start new week
        if not link[2] < weekstart+weekdelta:
            filename="week%s.pairs" % weekstart.strftime("%d%b%Y")
            print "Writing network file: ", filename, len(weekNetwork), "links"
            with open(filename,"w") as f:
                for edge in weekNetwork:
                    f.write("%i\t%i\n" % (edge[0],edge[1]))
            weekNetwork=[]
            weekstart+=weekdelta
            
        #add edges to week network
        s=email_ID_dict[link[0]]
        r=email_ID_dict[link[1]]
        #remove self loops
        if not s==r:
            #create undirected links
            if s<r:
                edge=(s,r)
            else:
                edge=(r,s)
            #check for duplicates
            if not edge in weekNetwork:
                weekNetwork.append(edge)

#old function!
#~ def get_email_list():
    #~ split_str='</data><data key="type">Email Address</data><data key="fullyObserved">true'
    #~ with open("../Enron_Dataset_v0.12.graphml") as f:
        #~ data=[line for line in f.readlines() if ('fullyObserved">true' in line)]
    #~ emails=[d.split(split_str)[0].split(">")[-1] for d in data]
    #~ return emails


def get_email_list():
    with open("addresses.txt") as f:
        addresses=[address.strip() for address in f.readlines()]
    return addresses


def get_email_addresses():
    print "Scanning mail for email addresses..."
    senders={}
    receivers=[]
    
    
    
    users = os.listdir("maildir")
    users.sort()
    for user in users:
        folders = os.listdir("maildir/"+user)
        folders.sort()
        nfolders = len(folders)
        for fno,folder in enumerate(folders):
            if folder.startswith("sent") or folder.startswith("_sent"):
                progress_str = "\r\t%i%%\t\t%s\t\tScanning folder:%s" % ((fno*100/nfolders),user,folder)
                stdout.write(progress_str.ljust(80))
                stdout.flush()
                path = "maildir/"+user+"/"+folder
                
                senders,receivers=process_dir(path,get_emails_from_file,(senders,receivers))
            
        stdout.write("\r\t100%%\t\tS=%i\t\t%s".ljust(80)  % (len(senders),user))
        stdout.write("\n")
        stdout.flush()
    return senders,receivers

def process_dir(path,file_parser,args):
    if os.path.isdir(path):
        for filein in os.listdir(path):
            args=process_dir(path+"/"+filein,file_parser,args)
    else:
        args=file_parser(path,*args)
    return args
    
def get_emails_from_file(path,senders,receivers):
    rec=False
    with open(path) as f:
        msg = f.readlines()
    for line in msg:
        if line.startswith("From"):
            sender = line.strip("From: ").strip()
            #~ if sender not in senders:
            if not senders.has_key(sender):
                #~ senders.append(sender)
                senders[sender]=0
            senders[sender]+=1
        if line.startswith("To"):
            rec=True
        if line.startswith("Subject"):
            rec=False
            if line.startswith("Subject: FW"):
                senders[sender]-=1
                if senders[sender]==0:
                    senders.pop(sender)
            break
        if rec:
            for receiver in line.strip("To: ").split():
                if receiver.strip(",") not in receivers:
                    receivers.append(receiver.strip().strip(","))
    return senders,receivers


def get_links():
    print "Getting email addresses..."
    addresses = get_email_list()
    print "Scanning mail for email links..."
    links=[]
    
    users = os.listdir("maildir")
    users.sort()
    for user in users:
        folders = os.listdir("maildir/"+user)
        folders.sort()
        nfolders = len(folders)
        for fno,folder in enumerate(folders):
            progress_str = "\r%i Links\t%i%%\t\t%s\t\tScanning folder:%s" % (len(links),(fno*100/nfolders),user,folder)
            stdout.write(progress_str.ljust(80))
            stdout.flush()
            path = "maildir/"+user+"/"+folder
            
            addresses,links=process_dir(path,get_links_from_file,(addresses,links))
            
        stdout.write("\r%i Links\t100%%\t\t%s".ljust(80)  % (len(links),user))
        stdout.write("\n")
        stdout.flush()
    addresses.sort()
    s,r,dts=zip(*links)
    order=argsort(dts)
    links = [links[link] for link in order]
    return addresses,links

def get_links_from_file(path,addresses,links):
    rec=False
    with open(path) as f:
        msg = f.readlines()
    for line in msg:
        if line.startswith("Date:"):
            datestamp=parse(line.strip("Date: ").strip())
        if line.startswith("From"):
            sender = line.strip("From: ").strip()
        if line.startswith("To"):
            rec=True
        if line.startswith("Subject"):
            rec=False
            break
        if rec:
            if sender in addresses:
                for receiver in line.strip("To: ").split():
                    if receiver.strip(",") in addresses:
                        links.append((sender,receiver.strip().strip(","),datestamp))
    return addresses,links
