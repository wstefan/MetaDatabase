# -*- coding: utf-8 -*-
"""
Created on Tue Aug  7 16:51:12 2012

@author: wstefan@mdanderson.org

A python script to add existing content to the meta database.
Run the script in the directory with the file name as argument.

"""

import MySQLdb,datetime,os,dateutil.parser
import time
from optparse import OptionParser
from metadbtools import *
import dicom

now=str(datetime.datetime.now());
t=time.time();
parser = OptionParser()

parser.add_option("-a","--author", dest="authorid", default="",help="file author")
parser.add_option("-s","--study", dest="studyid", default="", help="study id")
parser.add_option("-p","--path", dest="path", default="",help="path prefix")
parser.add_option("-l","--location", dest="location", default="",help="location")
parser.add_option("-t","--content_type", dest="type", default="",help="content type")
parser.add_option("-d","--description", dest="description", default="",help="description")
parser.add_option("-c","--access", dest="access", default="",help="access restrictions")
parser.add_option("-m","--meta", dest="meta", action="store_true", default=False, help="add meta data")
parser.add_option("-r","--remove", dest="remove", default="", help="remove meta data")
parser.add_option("-i","--dicom-scan", dest="scan", action="store_true", default=False, help="scan all sub-directories for dicoms. Add files with series description.")
parser.add_option("","--header", dest="header", default="", help="add dicom header to meta data")


(options, args) = parser.parse_args()

if len(args)==0: # No file name given: List files
    dir=os.getcwd();
    (location,path)=find_location(dir)
    if options.remove:
        (file_ids,meta_ids)=list_dir(location,path,dir,False)
        # print "removing %s" % options.remove
        if options.remove=="*":
            for i in file_ids.keys():
                c.execute("delete from external_files where id=%s" % file_ids[i])
                c.execute("delete from external_meta_info where file_id=%s" % file_ids[i])
                print "remove file %s with id %s" % ("%s" % i,file_ids[i])
        else:
            idx=options.remove.split(".")
            assert len(idx)==1 or len(idx)==2        
            if len(idx)==1:
                c.execute("delete from external_files where id=%s" % file_ids["%s" % idx[0]])
                c.execute("delete from external_meta_info where file_id=%s" % file_ids["%s" % idx[0]])
                print "remove file %s with id %s" % ("%s" % idx[0],file_ids["%s" % idx[0]])
            else:
                ist="%s.%s" % (idx[0],idx[1])
                c.execute("delete from external_meta_info where id=%s" % meta_ids[ist])
                print "remove metadata %s with id %s" % (ist,meta_ids[ist])
            
    else:
        list_dir(location,path,dir,prnt=True,read_dicom=True)   

elif options.meta: # -m option given: add meta data
   dir=os.getcwd();
   (location,path)=find_location(dir)
   if options.header=="":
       name= raw_input('Name        : ');
       if name=="redmine_project":
           value=choose_from_table("projects","id,name",0)
       else:
           value=raw_input('Value       : '); 

   print "Adding meta data for:"
   for f in args:
       c.execute("select f.path,s.name,f.description,a.name,f.id,f.study_id from external_files f LEFT JOIN studies s ON f.study_id=s.id LEFT JOIN access_ids a ON f.access_id=a.id where location=%s and path = \"%s/%s\" " % (location,path,f))    
       fn=c.fetchone();
       if fn is None:
           print "%s not in database. Add it to a project by calling 'metadata %s'" % (f,f)
       else:
           print "{0:30}|{1:40}|{2:30}|{3:20}".format(f,fn[1],fn[2],fn[3])
           if options.header=="":
               q = "insert into external_meta_info (study_id,file_id,name,value) values (0,%s,%s,%s)"
               v = (fn[4],name,value)  
               c.execute(q,v)
           else:
                try:
                    dcm=dicom.ReadFile(f)
                    h=dcm[eval("(%s)" % options.header)]
                    q = "insert into external_meta_info (study_id,file_id,name,value) values (0,%s,%s,%s)"
                    v = (fn[4],h.name,h.value)  
                    c.execute(q,v)
                except:
                    print " skipped, not a DICOM"       
                    
elif options.scan:
    if args[0]==".":
        dir=os.getcwd();
    else:
        dir=args[0];    
    options.authorid=choose_from_table("users","id,login",options.authorid)
    options.studyid=choose_from_table("studies","id,name",options.studyid,create_study)    
    # options.type=choose_from_table("content_types","id,name",options.type,create_content_type)   
    options.type=2;
    options.access=choose_from_table("access_ids","id,name",options.access)      
    if options.description=="":
       options.description=raw_input("Description (prefix): ")   
       
    if not(options.description==""):
        options.description+=". "
       
    c.execute("select login from users where id=%s" % options.authorid)
    print "Author-id   : %s (%s)" % (options.authorid,c.fetchone()[0]) 
    
    c.execute("select name from studies where id=%s" % options.studyid)
    print "Study-id    : %s (%s)" % (options.studyid,c.fetchone()[0])    
    
    c.execute("select name from content_types where id=%s" % options.type)
    print "Type        : %s (%s)" % (options.type,c.fetchone()[0]) 
    
    c.execute("select name from access_ids where id=%s" % options.access)
    print "Access      : %s (%s)" % (options.access,c.fetchone()[0]) 
    files=os.walk(dir);        
    for (dirname,dirnames,filenames) in files:
        (location,path)=find_location(dirname)
        for filename in filenames:  
            #print "%s/%s" % (dirname,filename)
            dcm=None;
            try:
                dcm=dicom.ReadFile("%s/%s" % (dirname,filename))
                h=dcm[eval("(0x8,0x103e)")]
                c.execute("select count(*) from external_files where location=%s and path=%s", (location,"%s/%s" % (path,filename)));
                if c.fetchone()[0]>0:
                    print "%s/%s allready in db" % (dirname,filename)
                else:
                    q = "insert into external_files (created_on,study_id,version,author_id,location,path,description,access_id,content_type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    v = (now,options.studyid,1,options.authorid,location,"%s/%s" % (path,filename),("%s%s") % (options.description,h.value),options.access,options.type)    
                    # print "%s" % (q % v)
                    c.execute(q,v)
                    print "%s/%s (%s) added" % (dirname,filename,("%s%s") % (options.description,h.value))
            except dicom.filereader.InvalidDicomError:
                print "%s/%s skipped; not a DICOM"  % (dirname,filename)
            except:
                raise
               
else: # add file to database
    if options.location=="":
        dir=os.getcwd();
        (options.location,options.path)=find_location(dir)
    
    
    options.authorid=choose_from_table("users","id,login",options.authorid)
    options.studyid=choose_from_table("studies","id,name",options.studyid,create_study)    
    options.type=choose_from_table("content_types","id,name",options.type,create_content_type)      
    options.access=choose_from_table("access_ids","id,name",options.access)     
    
    if options.description=="":
       options.description=raw_input("Description: ")     
        
    print 
    c.execute("select name from external_location where id=%s" % options.location)
    print "Location    : %s (%s)" % (options.location,c.fetchone()[0]) 
    
    print "Path        : %s" % options.path
    
    c.execute("select login from users where id=%s" % options.authorid)
    print "Author-id   : %s (%s)" % (options.authorid,c.fetchone()[0]) 
    
    c.execute("select name from studies where id=%s" % options.studyid)
    print "Study-id    : %s (%s)" % (options.studyid,c.fetchone()[0])    
    
    print "Description : %s" % options.description 
    
    c.execute("select name from content_types where id=%s" % options.type)
    print "Type        : %s (%s)" % (options.type,c.fetchone()[0]) 
    
    c.execute("select name from access_ids where id=%s" % options.access)
    print "Access      : %s (%s)" % (options.access,c.fetchone()[0]) 
    
    if not options.path=="" and not options.path.endswith("/"):
        options.path+="/";
        
    for a in args:
        q = "insert into external_files (created_on,study_id,version,author_id,location,path,description,access_id,content_type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        v = (now,options.studyid,1,options.authorid,options.location,"%s%s" % (options.path,a),options.description,options.access,options.type)    
        #print "%s" % (q % v)
        c.execute(q,v)
        print "%s added" % a
db.close()
