#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 09:35:15 2013

@author: wstefan
"""

import cgi,MySQLdb,datetime,os,dateutil.parser
from time import time
import Cookie
import crypt
import random
import traceback,sys,StringIO
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from metadbtools import *
import ast

def main_menu():
    print """<!DOCTYPE html>"""
    print 
    print "<A>META database</A>"
    print "Serach data set:"
    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<table>"
    print "<input type=\"hidden\" name=\"menu\" value=search_meta_db>"
    print "<input type=\"hidden\" name=\"group\" value=yes>"
    print "<table>"
    print "<tr><td><input type=\"text\" name=query>"
    print '<td><input type="submit" value="Go"></table></FORM>'
    print "List all studies: <a href=metaquery.py?menu=list_studies>here</a>"

def list_studies():
    c.execute("select s.name,s.description,s.id from studies s LEFT JOIN modality_ids m ON m.id=s.modality LEFT JOIN study_ids t on s.type_id=t.id group by s.id")
    st=c.fetchall();
    print "<h2>Studies:</h2>"
    print "<table bgcolor=gray>"
    print "<tr bgcolor=white><th>ID<th>Study name<th>description<th>"
    #c.execute("select s.name,s.description from studies s LEFT JOIN modality_ids m ON m.id=s.modality where s.description like \"%%%s%%\" or s.name like \"%%%s%%\" or m.name like \"%%%s%%\"" % (args[0],args[0],args[0]))
    for s in st:
        print "<tr bgcolor=white><td>%s<td><A href=metaquery.py?menu=show_study_files&study=%i&group=yes>%s</a><td>%s" % (s[2],s[2],s[0],s[1])

    print "</table>" 

def search_meta_db():

    print """<!DOCTYPE html>"""
    print
    query = form.getfirst('query','')
    grp = form.getfirst('group','')
    
    if grp=="yes":
        group="group by f.study_id,f.description";
    else:
        group="";
        

    if query=="":    
        print "<h1>Search Meta database</h1>"
        print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
        print "<table>"
        print "<input type=\"hidden\" name=\"menu\" value=search_meta_db>"
        print "<input type=\"hidden\" name=\"group\" value=yes>"
        print "<table>"
        print "<tr>Search:<td><input type=\"text\" name=query>"
        print '<tr><td><input type="submit" value="Go"></table></FORM>'
    else:
        c.execute("select s.name,s.description,s.id from studies s LEFT JOIN modality_ids m ON m.id=s.modality LEFT JOIN study_ids t on s.type_id=t.id where s.description like \"%%%s%%\" or s.name like \"%%%s%%\" or m.name like \"%%%s%%\" or t.name like \"%%%s%%\"" % (query,query,query,query))
        st=c.fetchall();
        print "<A href=metaquery.py>New search</A><br><br>"
        print "<h2>Studies:</h2>"
        if len(st)==0:
            print "no studies found"
        else:
            
            print "<table bgcolor=gray>"
            print "<tr bgcolor=white><th>Study name<th>description<th>"
            #c.execute("select s.name,s.description from studies s LEFT JOIN modality_ids m ON m.id=s.modality where s.description like \"%%%s%%\" or s.name like \"%%%s%%\" or m.name like \"%%%s%%\"" % (args[0],args[0],args[0]))
            for s in st:
                print "<tr bgcolor=white><td><A href=metaquery.py?menu=show_study_files&study=%i&group=yes>%s</A><td>%s" % (s[2],s[0],s[1]) 

            print "</table>" 
            
        print "<h2>Files:</h2>"   
        c.execute("select f.study_id,l.parameters,f.path,f.description,t.name from external_files f LEFT JOIN content_types t ON f.content_type=t.id LEFT JOIN external_location l on l.id=f.location where f.description like \"%%%s%%\" or f.path like \"%%%s%%\"  or t.name like \"%%%s%%\"  %s order by f.study_id" % (query,query,query,group))
        files= c.fetchall()
        if len(files)==0:
            print "no files found"
        else:
#            print "<table bgcolor=gray>"
#            print "<tr bgcolor=white><th>Study name<th>Study description<th>File name<th>File description<th>"   
            if grp=="yes":
                print "<A href=metaquery.py?menu=search_meta_db&query=%s>Ungroup Files</a>" % query
            else:
                print "<A href=metaquery.py?menu=search_meta_db&query=%s&group=yes>Group File descriptions</a>" % query

            print "<table bgcolor=gray>"
            study=0;
            for s in files:
                if not s[0]==study:
                    if not study==0:
                        print "</table>"
                        
                    c.execute("select name,description from studies where id=%s" % s[0])
                    st=c.fetchone()
                    print "<tr bgcolor=white><td><A href=metaquery.py?menu=show_study_files&study=%i&group=yes>%s</A><td>%s" % (s[0],st[0],st[1])
                    print "<tr bgcolor=white><td colspan=2><table>"
                    study=s[0];            
        
                print "<tr><td width=20 bgcolor=white>&nbsp;<td bgcolor=#EEEEEE>{0}/{1:100}<td bgcolor=#EEEEEE>{2:50}<td bgcolor=#EEEEEE>{3:40}".format(s[1],s[2],s[3],s[4])
        print "</table>"            
       
        
def show_study_files():
    print """<!DOCTYPE html>"""
    print
    
    study = form.getfirst('study','')
    grp = form.getfirst('group','')
    query = form.getfirst('query','')
    
    if grp=="yes":
        group="group by f.description";
    else:
        group="";
    
    c.execute("select s.name,s.description,s.id,m.name,t.description from studies s LEFT JOIN modality_ids m ON m.id=s.modality LEFT JOIN study_ids t on s.type_id=t.id where s.id=%s" % (study) )
    st=c.fetchone();
    print "<A href=metaquery.py>New search</A><br><br>"
    print "<h1>Study:</h1>"
    print "<table bgcolor=gray>"
    print "<tr bgcolor=white><td><b>ID:</b><td>%s" % st[2] 
    print "<tr bgcolor=white><td><b>Name:</b><td>%s" % st[0]
    print "<tr bgcolor=white><td><b>Description:</b><td>%s" % st[1]
    print "<tr bgcolor=white><td><b>Modality:</b><td>%s" % st[3]
    print "<tr bgcolor=white><td><b>Study type:</b><td>%s" % st[4]
    print "</table>"
    print "Search study: "
    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<table>"
    print "<input type=\"hidden\" name=\"menu\" value=show_study_files>"
    print "<input type=\"hidden\" name=\"group\" value=%s>" % grp
    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
    print "<table>"
    print "<tr><td><input type=\"text\" name=\"query\" value=\"%s\">" % query
    print '<td><input type="submit" value="Go"></table></FORM>'
    # print "<A>edit</a>"
    print "<h1>Files:</h1>"
    
    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<input type=\"hidden\" name=\"menu\" value=show_study_files>"
    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
    print "<input type=\"hidden\" name=\"query\" value=\"%s\">" % query
    if grp=="yes":
        print '<input type="submit" value="Un-group Files"></FORM>'
    else:
        print "<input type=\"hidden\" name=\"group\" value=\"yes\">" 
        print '<input type="submit" value="Group Files"></FORM>'
    

    if query=="":    
        c.execute("select f.study_id,l.parameters,f.path,f.description,t.name,a.name,f.id from external_files f LEFT JOIN content_types t ON f.content_type=t.id LEFT JOIN external_location l on l.id=f.location left join access_ids a on a.id=f.access_id where f.study_id=%s %s" % (study,group))
    else:
        c.execute("select f.study_id,l.parameters,f.path,f.description,t.name,a.name,f.id from external_files f LEFT JOIN content_types t ON f.content_type=t.id LEFT JOIN external_location l on l.id=f.location left join access_ids a on a.id=f.access_id where f.study_id=%s and f.description like \"%%%s%%\" %s" % (study,query,group))
 
    print "<table bgcolor=white>"
    print "<tr bgcolor=#DDDDDD><th>File name<th>Description<th>Type<th>Access restrictions"    
    for f in c.fetchall():          
        print "<tr  bgcolor=#EEEEEE><td>{0}/{1:100}<td>{2:50}<td>{3:40}<td>{4:40}".format(f[1],f[2],f[3],f[4],f[5])
        c.execute("select name,value,id from external_meta_info where file_id=%s" % (f[6]))
        res=c.fetchall();
        if len(res)>0:
            print "<tr><td colspan=4><table>"
            for e in res:
                print "<tr><td>&nbsp;<td>%s=%s" % (e[0],e[1])   
            print "</table>"
                
            
    print "</table>"
                

def get_study_list():
    c.execute("select id,name,description from studies")
    print    
    for e in c.fetchall():
        print e[1]


print "Content-Type: text/html"
print 
try: 
    menu=""
    revision="$Revision: 1 $"
    revision=str.replace(revision,"$Revision: ","");
    revision=str.replace(revision," $","");

    now=datetime.datetime.utcnow()
    
    form = cgi.FieldStorage()     
    menu = form.getfirst('menu','main') 
    if menu=="main":
        main_menu()
    elif menu=="get_study_list":
        get_study_list()
    elif menu == "search_meta_db":
        search_meta_db()
    elif menu == "show_study_files":    
        show_study_files()
    elif menu == "list_studies":
        list_studies()
    else:
        print "unknown menu selection"
    
except:
    raise
    