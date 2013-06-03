# -*- coding: utf-8 -*-
"""
Created on Fri May 31 14:31:42 2013

@author: wstefan
"""
import sys


filename = sys.argv[1]
if filename is not None:
    from metadbtools import *
    import dicom
  
    now=str(datetime.datetime.now());
    
    authorid=-1;
    location=2;
    access=4;
    type=2;
    
    c.execute("select id from external_files where path=%s",filename)
    ids=c.fetchall()        
    if len(ids)>0:
        for id in ids:
            c.execute("delete from external_files where id=%s", id[0])
            c.execute("delete from external_meta_info where file_id=%s", id[0])
            print "%s deleted" % (filename) 
    
    dcm = dicom.read_file("/DICOM_pushed/%s" % filename)
    description=dcm.SeriesDescription;
    Pid=dcm.PatientID;
    c.execute("select id from studies where type_id=4 and MRN=%s" , Pid)
    res=c.fetchall();
    if len(res)==1:
        studyid=res[0][0];
    else:
        studyid=17; # DICOM in
    
    q = "insert into external_files (created_on,study_id,version,author_id,location,path,description,access_id,content_type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    v = (now,studyid,1,authorid,location,filename,description,access,type)    
    # print "%s" % (q % v)
    c.execute(q,v)
   
    c.execute('select id from external_files where path=%s',filename)
    fid=c.fetchone()[0]
    print "%i: %s (%s) added" % (fid,filename,description)
    try:
        c.execute('insert into external_meta_info (file_id,name,value) values (%s,"Study_ID",%s)',(fid,dcm.StudyID))
    except:
        pass
    
    try:   
        c.execute('insert into external_meta_info (file_id,name,value) values (%s,"Series_Number",%s)',(fid,dcm.SeriesNumber))
    except:
        pass
 

    try:   
        c.execute('insert into external_meta_info (file_id,name,value) values (%s,"Series_Date",%s)',(fid,dcm.SeriesDate))
    except:
        pass
    
    
