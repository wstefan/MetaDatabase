# -*- coding: utf-8 -*-
"""
Created on Mon Aug 13 18:31:10 2012

@author: -
"""

import MySQLdb,datetime,os,dateutil.parser
import time
from optparse import OptionParser
from metadbtools import *

now=str(datetime.datetime.now());
t=time.time();
parser = OptionParser()

parser.add_option("-s","--study", action="store_true", dest="studies", default=False, help="search studies")
parser.add_option("-f","--files", action="store_true", dest="files", default=False, help="search files")
parser.add_option("-m","--meta", action="store_true", dest="meta", default=False, help="search meta data")
parser.add_option("-g","--group", action="store_true", dest="group", default=False, help="group file type")


(options, args) = parser.parse_args()


if options.group:
    group="group by f.study_id,f.description";
else:
    group="";

if options.studies:
    c.execute("select s.name,s.description,s.id from studies s LEFT JOIN modality_ids m ON m.id=s.modality LEFT JOIN study_ids t on s.type_id=t.id where s.description like \"%%%s%%\" or s.name like \"%%%s%%\" or m.name like \"%%%s%%\" or t.name like \"%%%s%%\"" % (args[0],args[0],args[0],args[0]))
    st=c.fetchall();
    if len(st)==0:
        print "no studies found"
    else:
        print "Studies:"
        print "="*152
        #c.execute("select s.name,s.description from studies s LEFT JOIN modality_ids m ON m.id=s.modality where s.description like \"%%%s%%\" or s.name like \"%%%s%%\" or m.name like \"%%%s%%\"" % (args[0],args[0],args[0]))
        for s in st:
            print "{0:50}: {1:100}".format(s[0],s[1])
            c.execute("select f.study_id,l.parameters,f.path,f.description,t.name from external_files f LEFT JOIN content_types t ON f.content_type=t.id LEFT JOIN external_location l on l.id=f.location where f.study_id=%s %s" % (s[2],group))
            for f in c.fetchall():          
                print "  {0}/{1:100}: {2:50}: {3:40}".format(f[1],f[2],f[3],f[4])
            
            print  
    


 
if options.files:  
    c.execute("select f.study_id,l.parameters,f.path,f.description,t.name from external_files f LEFT JOIN content_types t ON f.content_type=t.id LEFT JOIN external_location l on l.id=f.location where f.description like \"%%%s%%\" or f.path like \"%%%s%%\"  or t.name like \"%%%s%%\"  %s order by f.study_id" % (args[0],args[0],args[0],group))
    files= c.fetchall()
    if len(files)==0:
        print "no files found"
    else:
        print "Files:"
        print "="*152    
        study=0;
        for s in files:
            if not s[0]==study:
                if not study==0:
                    print 
                c.execute("select name,description from studies where id=%s" % s[0])
                st=c.fetchone()
                print "Study: {0:50}: {1:100}".format(st[0],st[1])
                print "-"*152 
                study=s[0];            
    
            print "  {0}/{1:100}: {2:50}: {3:40}".format(s[1],s[2],s[3],s[4])
    print 

if options.meta:    
    c.execute("select f.study_id,f.id,l.parameters,f.path,f.description,m.name,m.value from external_files f LEFT JOIN external_meta_info m ON m.file_id=f.id LEFT JOIN external_location l on l.id=f.location where m.value like \"%%%s%%\" or  m.name like \"%%%s%%\" %s order by f.study_id,f.id" % (args[0],args[0],group))
    meta=c.fetchall()
    if len(meta)==0:
        print "no meta data found"
    else:
        print "Meta data:"
        print "="*152    
        id=0;    
        study=0;
        for s in meta:
            if s[5]=="redmine_project": 
                c.execute("select name from projects where id=%s" % s[6])
                mval=c.fetchone()[0]
            else:
                mval=s[6]
                
            if not s[0]==study:
                if not study==0:
                    print 
                c.execute("select name,description from studies where id=%s" % s[0])
                st=c.fetchone()
                print "Study: {0:50}: {1:100}".format(st[0],st[1])
                print "-"*152 
                study=s[0];            
                
            if not s[1]==id:
                print "  {0}/{1:50}: {2:100}".format(s[2],s[3],s[4])
                id=s[1];
            print "     {0:30}: {1:100}".format(s[5],mval)
    print


  
db.close()