# -*- coding: utf-8 -*-
"""
Created on Fri May 31 14:31:42 2013

@author: wstefan
"""
import sys,time
import os,sys
from metadbtools import *
import dicom,re

def getAutoRules():
    c.execute("select id from studies where type_id=4");
    studies=[];
    AutoRules={};
    for i in c.fetchall():
       c.execute("select name,value from external_meta_info where study_id=%s and name like \"route:%%\"",i[0]);
       auto_rules=c.fetchall() 
       AutoRules[i[0]]=auto_rules
       
    return AutoRules;

def getAutoDest(dcm):
    #c.execute("select id from studies where type_id=4");
    studies=[];
    for i in AutoRules.keys():
        #c.execute("select name,value from external_meta_info where study_id=%s and name like \"route:%%\"",i[0]);
        auto_rules=AutoRules[i]
        if len(auto_rules)>0:
            go=True;
            for r in auto_rules:
               tag = r[0].split(":")
               try:
                   dtag=dcm[eval("(%s)" % tag[1])]
                   if r[1].startswith("=~"):
                       v=r[1][2:];
                       p=re.compile(v);
                       result= p.match(dtag.value) is not None
                       print "%s: %s =~ %s (%s)" % (dtag.name,dtag.value,v,result) 
                       
                   else:
                       v=r[1][1:];
                       result=dtag.value==v
                       print "%s: %s = %s (%s) " % (dtag.name,dtag.value,v,result)
               
                   if len(tag)==2 or tag[2]=="and":
                       go = go and result
                   elif tag[2]=="or":
                       go = go or result
                   
               except:
                   go=False;
                   
        else:
            go=False
        
        if go:
            studies.append(i)
        #print "%s: %s" % (i[0],go)
    return studies

sid=1;
spath="dicom_meta_db";
sloc="/FUS4/%s" % spath;

single=False;
simulate=False;

if not single:
    f=open("%s/import/ping" % (sloc),"w");
    f.write('ping');
    time.sleep(10);
    if not os.path.exists("%s/import/ping" % sloc):
       print "daemon is running"
       sys.exit()
   
   
print "Starting new daemon"

go=True;
while(go):
   AutoRules=getAutoRules()
   files = os.listdir("%s/import" % sloc ) 
   
   for filename   in files:

       if not simulate:
           if os.path.isfile("%s/import/ping" % (sloc)):
               try:
                  os.system("rm %s/import/ping" % (sloc));
               except:
                  pass
        
               if filename=="ping":
                  continue      

       now=str(datetime.datetime.now());
    
       authorid=-1;
       location=sid;
       access=4;
       type=2;

       try:
          dcm = dicom.read_file("%s/import/%s" % (sloc,filename))
       except:
          continue

       stuid=dcm.StudyInstanceUID;
       seuid=dcm.SeriesInstanceUID;
       
       if not simulate:
           if not os.path.exists("%s/%s" % (sloc,stuid)):
              os.system("mkdir %s/%s" % (sloc,stuid));
    
           if not os.path.exists("%s/%s/%s" % (sloc,stuid,seuid)):
            os.system("mkdir %s/%s/%s" % (sloc,stuid,seuid));
    
           os.system("chmod a+rw %s/import/%s" % (sloc,filename))
           os.system("mv %s/import/%s %s/%s/%s/" % (sloc,filename,sloc,stuid,seuid));
           filename="%s/%s/%s/%s" % (spath,stuid,seuid,filename);    

           c.execute("select id from external_files where path=%s",filename)
           ids=c.fetchall()        
           if len(ids)>0:
               for id in ids:
                   c.execute("delete from external_files where id=%s", id[0])
                   c.execute("delete from external_meta_info where file_id=%s", id[0])
                   print "%s deleted" % (filename) 
    

       try:
          description=dcm.SeriesDescription;
       except:
          description=""

       studyids=getAutoDest(dcm);

       #Pid=dcm.PatientID;
       #c.execute("select id from studies where type_id=4 and MRN=%s" , Pid)
       #res=c.fetchall();
       if len(studyids)==0:
           studyids=(17,); # DICOM i
           
           
       for studyid in studyids:
           print "adding %s to study %s" % (filename,studyid)
        
           q = "insert into external_files (created_on,study_id,version,author_id,location,path,description,access_id,content_type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
           v = (now,studyid,1,authorid,location,filename,description,access,type)    
           # print "%s" % (q % v)
           if not simulate:
               c.execute(q,v)
       
               c.execute('select id from external_files where path=%s',filename)
               fid=c.fetchone()[0]
               print "%i: %s (%s) added" % (fid,filename,description)
               #      date, stationname,study UID, series UID,study description 
               tags=['0x8,0x21','0x8,0x1010','0x20,0xd','0x20,0xe','0x8,0x1030']
               c.execute("select value from external_meta_info where study_id=%s",studyid)
               for t in c.fetchall():
                   tags.append(t[0])
                   
               for t in tags:
                   try:
                       h=dcm[eval("(%s)" % t)]
                       c.execute('insert into external_meta_info (file_id,name,value) values (%s,%s,%s)',(fid,h.name,h.value))
                   except:
                       pass
           else:
               print "%s" % (q % v) 
    
   time.sleep(5);
   go=not single;