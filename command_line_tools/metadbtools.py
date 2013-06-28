# -*- coding: utf-8 -*-
"""
Created on Mon Aug 13 18:29:17 2012

@author: -
"""

import MySQLdb,datetime,os,dateutil.parser
import time
import dicom
from optparse import OptionParser

def parse_config(filename):
    COMMENT_CHAR = '#'
    OPTION_CHAR =  '='
    options = {}
    f = open(filename)
    for line in f:
        # First, remove comments:
        if COMMENT_CHAR in line:
            # split on comment char, keep only the part before
            line, comment = line.split(COMMENT_CHAR, 1)
        # Second, find lines with an option=value:
        if OPTION_CHAR in line:
            # split on option char:
            option, value = line.split(OPTION_CHAR, 1)
            # strip spaces:
            option = option.strip()
            value = value.strip()
            # store in dictionary:
            options[option] = value
    f.close()
    return options
 
 
def find_location(dir):
    c.execute("select id,parameters from external_location where type=\"local\"")
    loc=[];
    for e in c.fetchall():
        # print "%s starts with %s" % (dir,e[1])
        if dir.startswith(e[1]):
            loc.append(e[0])
            prefix_length=len(e[1]);
    if len(loc)>1:
        for l in loc:
            print "ERROR: more than one location"
    elif len(loc)==0:
        return (None,None)
            
    assert len(loc)==1        
    location=loc[0]
    path=dir[prefix_length+1:];
    return (location,path)       
    
def choose_from_table(table,fields,choice=0,new_callback=None):
    try:
        choice=int(choice);
    except:
        choice=0;
    c.execute("select %s from %s where id=%s" % (fields,table,choice));
    if c.fetchone() is None:
        ids=[];
        while(not ids.__contains__(int(choice))): 
            print 
            if new_callback is not None:
                print "Please select from the list or enter \"n\" for new."
            else:
                print "Please select from:"
            c.execute("select %s from %s" % (fields,table))
            for s in c.fetchall():
                print "%s: %s" % s
                ids.append(int(s[0]));
               
            choice=raw_input('id: ')
            if choice=="n" and new_callback is not None:
                new_callback()
                choice=0;
            else:
                try:
                    choice=int(choice);
                except:
                    choice=0;
    return choice

def create_content_type():
    name       =raw_input('Name        : ');
    q="insert into content_types (name) values (%s)"
    v=(name)
    c.execute(q,v);
    
def create_study_type():
    name       =raw_input('Name        : ');
    description=raw_input('Description : ');   
    q="insert into study_ids (name,description) values (%s,%s)"
    v=(name,description)
    c.execute(q,v);
    
def create_study():
    now=datetime.datetime.utcnow()
    name       =raw_input('Name        : ');
    description=raw_input('Description : ');
    type=choose_from_table("study_ids","id,name",0,create_study_type);
    mod=choose_from_table("modality_ids","id,name");
    mrn=raw_input('MRN         : ');   
    q="insert into studies (created_on,name,description,type_id,modality,MRN) values (%s,%s,%s,%s,%s,%s)"
    v=(now,name,description,type,mod,mrn)
    c.execute(q,v);

def list_dir(location,path,dir,prnt=True,read_dicom=False):
    meta_ids={}; # store meta and file ids to edit or delete
    file_ids={};
    c.execute("select f.path,s.name,f.description,a.name,m.value,f.id from external_files f LEFT JOIN studies s ON f.study_id=s.id LEFT JOIN access_ids a ON f.access_id=a.id left join external_meta_info m on m.file_id=f.id where location=%s and path like \"%s%%\" group by f.id" % (location,path))    
    dbfiles=c.fetchall();
    if prnt:
        print "{0:30}|{1:40}|{2:30}|{3:20}".format("","study name","document description","access") 
        print "-"*123 
    i=0;
    for filename in os.listdir("."):
        j=0;       
        ent=[];        
        for dbf in dbfiles: # Search database for filename 
            if dbf[0].endswith(filename):
                ent=dbf;
                
        if len(ent)>0:
            i+=1;
            file_ids["%i" % (i)]=ent[5];
            if prnt:
                 print "{0:6}: {1:30}|{2:40}|{3:30}|{4:20}".format("%i" % (i),filename,ent[1],ent[2],ent[3])
                 
            if ent[4] is not None: # display meta data
                c.execute("select name,value,id from external_meta_info where file_id=%s" % (ent[5]))    
                for m in c.fetchall():
                    j+=1;
                    
                    meta_ids["%i.%i" % (i,j)]=m[2];
                    if prnt:
                        if m[0]=="redmine_project":
                            c.execute("select name from projects where id=%s" % m[1])
                            print "{0:6}:   {1:10}: {2:40}".format("%i.%i" % (i,j), m[0],c.fetchone()[0]) 
                        else:
                            print "{0:6}:   {1:10}: {2:40}".format("%i.%i" % (i,j),m[0],m[1]) 
        else:
            if prnt:
                try:
                    dcm=dicom.read_file(filename)
                    print "        {0:30}: DICOM: {1:50}".format(filename,dcm.SeriesDescription)
                except:
                    print "        {0:30}".format(filename)
        
            
    return (file_ids,meta_ids)
    
    
def makeCombQuery(file_fields,meta_fields,where='',group=False):
    q="select %s" % file_fields[0];
    for i in range(1,len(file_fields)):
        q+=",%s" % file_fields[i]
        
    for i in range(0,len(meta_fields)):
        s = meta_fields[i].split("=");
        if s[0].startswith("*"):
            s[0]=s[0][1:];
        q+=", m%i.value as `%s` " % (i,s[0])
            
    q+=" from external_files f \n";
    for i in range(0,len(meta_fields)):
        s = meta_fields[i].split("=");
        if s[0].startswith("*"):
            s[0]=s[0][1:];
            q+=" left join external_meta_info m%i on m%i.file_id=f.id and m%i.name=\"%s\" " % (i,i,i,s[0])
        else:
            q+=" join external_meta_info m%i on m%i.file_id=f.id and m%i.name=\"%s\" " % (i,i,i,s[0])
            
        if len(s)>1:
            q+=" and m%i.value=\"%s\" " % (i,s[1])
            
        q+="\n"
        
    if not where == '':
        q+= "where %s\n" % where
            
    if group:
        q+= "group by m0.value"
        for i in range(1,len(meta_fields)):
            q+= ",m%i.value" % i
        q+="\n"
  
  
    return q
   
    
    
cf = parse_config('/etc/metadbconfig.cfg')   
try:
    db=MySQLdb.connect(host=cf["mysql_server"],user=cf["mysql_user"],passwd=cf["mysql_password"],db=cf["mysql_db"])  
    c=db.cursor()
except:
    raise
