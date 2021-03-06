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
import urllib

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
    print "List all studies: <a href=metaquery.py?menu=list_studies>here</a><br>"
    print "DICOM inbox (pushed files): <a href=metaquery.py?menu=DICOM_in_box>here</a>"
    print "<br><br><A href=http://172.30.205.56/mediawiki/index.php/IGI_meta_database>Wiki help page</A>"

def meta_query():
    meta = form.getlist('meta')    
    study = form.getfirst('study','')  
    pform = form.getfirst('pform','edit')
    N = int(form.getfirst('nmeta','10')) # number of meta fields in edit mode
    order = int(form.getfirst('order','-1'))
    if pform=="edit":
        print """<!DOCTYPE html>"""
        print 
        print "<h1>Query study %s:</h1>" % study 
        print "<h2>Enter meta fields:</h2>"
        print "examples:<ul>"
        print "<li>class=MR_ACR_s1_sag_phantom (only display files with a meta tag class=MR_ACR_s1_sag_phantom)"
        print "<li>class (only display files with a meta tag class)"
        print "<li>*class (display meta tag class if it exists or not)"
        print "</ul>"
        print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
        print "<input type=\"hidden\" name=\"menu\" value=meta_query>"
        print "<input type=\"hidden\" name=\"study\" value=%s>" % study 
        print "<input type=\"hidden\" name=\"nmeta\" value=%i>" % (N+5);
        print "<table>"
        print "<tr><th>Sort<th>meta tag"
        for i in range(N):
            print "<tr>"
            print "<td><input type=\"radio\" name=\"order\" value=\"%i\">" % i
            if i<len(meta):
                print "<td colspan=2><input type=\"input\" name=\"meta\" value=\"%s\">" % meta[i]
            else:
                print "<td colspan=2><input type=\"input\" name=\"meta\" >"
                
        print "<tr><td>format:<td><select name=\"pform\">"
        print '  <option value=html>HTML</option>'
        print '  <option value=csv>csv</option>'
        print '  <option value=edit>more fields</option>' 
        print '</select>'
        print '<tr><td><input type="submit" value="Go"></FORM>'
    else:
        q=makeCombQuery(('f.id',),meta,group=False,where='f.study_id=%s' % study);
        #print "<pre>%s</pre>" % q
        if order>-1:
            c.execute("%s order by m%i.value" % (q,order))
        else:
            c.execute("%s" % (q))
            
        if pform=="html":
            print """<!DOCTYPE html>"""
            print 
            
            print "<table bgcolor=gray><tr bgcolor=white>"
            for t in c.description:
                print "<th>%s" % t[0]
            
            for e in c.fetchall():
                print "<tr bgcolor=white>"
                for d in e:
                    try:
                        if d.startswith('http'):
                            print "<td><A href=%s target=_blank>%s</A>" % (d,d)
                        else:
                            print "<td>%s" % d
                    except:
                        print "<td>%s" % d  
                        
            print "</table><table><tr>"
            print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
            print "<input type=\"hidden\" name=\"menu\" value=meta_query>"
            print "<input type=\"hidden\" name=\"study\" value=%s>" % study 
            print "<input type=\"hidden\" name=\"order\" value=%s>" % order 
            for m in meta:
                print "<input type=\"hidden\" name=\"meta\" value=\"%s\">" % m
            print "<td>format:<td><select name=\"pform\">"
            print '  <option value=html>HTML</option>'
            print '  <option value=csv selected>csv</option>'
            print '  <option value=graph selected>graph</option>'
            print '  <option value=edit selected>edit query</option>' 
            print '</select>'
            print '<td><input type="submit" value="Go"></FORM></table>'
        elif pform=="csv":
            first=True;
            print "Content-Type: text/csv"     
            print
            for t in c.description:
                if not first:
                    print "\t\"%s\"" % t[0],
                else:
                    print "\"%s\"" % t[0],
                    first=False;
            print ""
            
            for e in c.fetchall():
                first=True;
                for d in e:
                    if not first:
                        print "\t\"%s\"" % d,
                    else:
                        print "\"%s\"" % d, 
                        first=False;
                print
        elif pform=='graph':  
            import matplotlib
            matplotlib.use('Agg')
            from PIL import Image
            import matplotlib.pyplot as plt
            import numpy as np
            import cStringIO
            
            xaxis = form.getfirst('xaxis','1')
            yaxis = form.getlist('yaxis')
        
            if len(yaxis)==0:
                yaxis= (len(meta),)
            
            data=c.fetchall()            
            dplot=np.zeros((len(data),len(yaxis))) 
            xticks=[]
            for i in range(len(data)):
                xticks.append(data[i][int(xaxis)])
                for j in range(len(yaxis)):
                    dplot[i,j]=float(data[i][int(yaxis[j])])
                
            fig=plt.figure(figsize=(10,5))
            plot1= fig.add_subplot ( 111 )
            x=range(len(data))
            plot1.plot(x,dplot)
            sp=int(np.floor(len(data)/20));
            xl=x[0::sp]; xl[-1]=x[-1]
            xt=xticks[0::sp]; xt[-1]=xticks[-1];
            
            plt.xticks(xl,xt,size=8,rotation=45)
#            plt.ylim([-50, 50])
            plt.xlabel("%s" % meta[int(xaxis)])
            yl="";
            leg=[];
            for y in yaxis:
                yl+=" "+meta[int(y)-1]
                leg.append(meta[int(y)-1])
                
            plt.legend(leg,loc=3)
            plt.title("%s" % yl)
            I=fig2img(fig); 
            f = cStringIO.StringIO()
            I.save(f, "PNG")
            f.seek(0)
            im_data=f.read()
            
#            print "Content-Type: text/text"     
#            print
#            print str(dplot)
      
            print "Content-type: image/png\n"    
            print im_data

def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    import numpy as np;
    fig.canvas.draw ( )
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = np.fromstring ( fig.canvas.tostring_argb(), dtype=np.uint8 )
    buf.shape = ( w, h,4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = np.roll ( buf, 3, axis = 2 )
    return buf
                
            

def fig2img ( fig ):
    from PIL import Image
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.fromstring( "RGBA", ( w ,h ), buf.tostring( ) )    
    
            
def make_image(dcm,level='',win='',size=None):
    #import Image, ImageDraw
    from PIL import Image
    import numpy as np
    
    I=dcm.pixel_array.astype('float');              # Get image from dicom
    try:
        I=I+float(dcm.RescaleIntercept);
    except:
        pass
    # window image   
    
    if level == '':        
        try:
            I=I-float(dcm.WindowCenter);
            win=dcm.WindowWidth;
            I=np.minimum(np.maximum(I,-float(win)/2),float(win)/2)  
        except:
            pass

    else:
        I=I-float(level);
        I=np.minimum(np.maximum(I,-float(win)/2),float(win)/2)                                 # Normalize intensity 

    if not size is None: 
        try:
            from scipy.signal import resample
            I=resample(I, float(size),axis=0);
            I=resample(I, float(size),axis=1);
        except:
            raise

    #normalize to display
    I=I-np.amin(I);                                 # Normalize intensity 
    I=I/np.amax(I);
    return Image.fromarray((I*255).astype('uint8'))

def getDICOMImage():
    import cStringIO
    file_id = form.getfirst('file_id','')
    size = form.getfirst('size',None)
    wl = cgi.escape(form.getfirst('WL',''))
    ww = cgi.escape(form.getfirst('WW',''))

#    import matplotlib
#    matplotlib.use('Agg')
#    import matplotlib.pyplot as plt
    
    c.execute("select concat(l.parameters,'/',f.path) as path from external_files f join external_location l on l.id=f.location and f.id=%s;" , file_id )
    path=c.fetchone()[0]

    dcm=dicom.read_file(path);
    I=make_image(dcm,wl,ww,size)
    f = cStringIO.StringIO()
    I.save(f, "PNG")
    f.seek(0)
    im_data=f.read()

    print "Content-type: image/png\n"    
    print im_data
 
    

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
    print "<A href=metaquery.py?menu=edit_study>New Study</A>"
    
def DICOM_in_box():
    print "<h2>Inbox:</h2>" 
    c.execute("select id,name from studies");
    studies=c.fetchall();    
    
    s=makeCombQuery(('f.id','f.path','count(*)'),('*Study Description','*Study Instance UID','*Series Date'),group=True,where='f.study_id=17')
    #print "<pre>%s</pre>" % s
    c.execute(s)
    st=c.fetchall();
    print "<table bgcolor=gray>"
    print "<tr bgcolor=white><th>#files<th>Study Description<th>Study UID"
    for e in st:
        print "<tr bgcolor=white><td>%s<td>%s<td>%s" % (e[2],e[3],e[4])
        s=makeCombQuery(('f.id','f.description','count(*)'),('Study Instance UID=%s' % str(e[4]),'Series Date=%s' % str(e[5])),group=False,where='f.study_id=17')
        #print "<pre>%s</pre>" % s
        c.execute("%s group by f.description" %s )
        print "<tr bgcolor=white><td><td colspan=2><table bgcolor=white>"
        for f in c.fetchall():
            print "<td>%s, " % f[1]
        print "</table>"
        s=makeCombQuery(('f.id','f.description'),('Study Instance UID=%s' % str(e[4]),'Series Date=%s' % str(e[5])),group=False,where='f.study_id=17')        
        c.execute("%s limit 21" % s )
        r=c.fetchall()
        print "<tr bgcolor=white><td><td colspan=2><table bgcolor=white><td>"
        l=min(21,len(r))
        for f in r[0:l]:
            print "<A href=\"http:metaquery.py?menu=getDICOMImage&file_id=%s&pform=PNG\"><image src=\"http:metaquery.py?menu=getDICOMImage&file_id=%s&pform=PNG&size=100\"></A>"% (f[0],f[0])
        if len(r)>20:
            print "..."
        print "</table>"
        print "<tr bgcolor=white><td><td colspan=2>"
        print "<table><tr><td>Move to study: "
        print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
        print "<input type=\"hidden\" name=\"menu\" value=add_to_study>"
        print "<input type=\"hidden\" name=\"query\" value=\"Study Instance UID=%s\">" % str(e[4])
        print "<select name=\"study_id\">"
        for study in studies:
            print "<option value=\"%i\">%s" % (study[0],study[1])
        print "</select>"
        print '<td><input type="submit" value="Go"></FORM>'
        print "</table>"
        
    print "</table>" 
    print "List all studies: <a href=metaquery.py?menu=list_studies>here</a><br>"
    print "DICOM inbox (pushed files): <a href=metaquery.py?menu=DICOM_in_box>here</a><br>"
    print "<A href=metaquery.py?menu=edit_study>Create new Study</A>"

def add_to_study():
    print """<!DOCTYPE html>"""
    print
    study_id = form.getfirst('study_id','')
    old_study_id= form.getfirst('old_study_id','17')
    query  = form.getfirst('query','');
      
    q = get_meta_query(old_study_id,query);

    #print "<pre>%s</pre>" % q 
    c.execute(q)
    files=c.fetchall();

    #c.execute("select f.id,f.path from external_files f join external_meta_info m on f.id=m.file_id and m.name=\"Study Instance UID\" and m.value=%s and f.study_id=%s", (STUID,old_study_id) ) 
    #st=c.fetchall();
    print "moving:<br><pre>"
    for s in files:
        print "%s (%s->%s) , %s/%s" % (s[6],old_study_id,study_id,s[1],s[2])
        c.execute("update external_files set study_id=%s where id=%s", (study_id,s[6]))
    print "</pre>"
    print "List all studies: <a href=metaquery.py?menu=list_studies>here</a><br>"
    print "Back to last Study: <a href=metaquery.py?menu=show_study_files&study=%s&group=yes>here</a>" % old_study_id

def send_to_dicom_node():
    print """<!DOCTYPE html>"""
    print
    study = form.getfirst('study','');
    query  = form.getfirst('query','');
    node  = form.getfirst('dicom_node','');
    
    c.execute("select ip,port,aetitle from dicom_destinations where id=%s", node);
    dicom_node=c.fetchone();
    
    q = get_meta_query(study,query);

    #print "<pre>%s</pre>" % q 
    c.execute(q)
    files=c.fetchall();
    
    print "sending..<br><pre>"
    st0 = "storescu %s %s -aet WS_PACS -aec %s" % (dicom_node[0],dicom_node[1],dicom_node[2])

    batch=50;    
    
    st=st0;
    for i in range(len(files)):
        filename="%s/%s" % (files[i][1],files[i][2])
        st+=" %s" % filename
        if i % batch == (batch-1):
           print st
           os.system(st) 
           st=st0;

    if not st==st0:
        print st
        os.system(st)
    print "</pre>"
    print "done.<br>"
    print "List all studies: <a href=metaquery.py?menu=list_studies>here</a><br>"
    print "Back to last Study: <a href=metaquery.py?menu=show_study_files&study=%s&group=yes>here</a>" % study
    
    


def get_meta_query(study,query,grp=''):
    # get sql query string for a query in a study including grouping
    q1="select f.study_id,l.parameters,f.path,f.description,t.name,a.name,f.id,f.content_type"
    q2="LEFT JOIN content_types t ON f.content_type=t.id LEFT JOIN external_location l on l.id=f.location left join access_ids a on a.id=f.access_id"
    if grp=="":
        q1+=",1"
        q3="";
    else:
        q1+=",count(*)"
        if grp=="yes":
            q3="group by f.description"
        else:
            q2+=" join external_meta_info m on f.id=m.file_id and m.name=\"%s\"" % grp
            
            q3="group by m.value"
 
    if query=="":
        q4=""
    else:
        sp=query.split("=")
        if len(sp)==2:
            q2+=" join external_meta_info m1 on f.id=m1.file_id and m1.name=\"%s\"" % sp[0]
            q4= " and m1.value = \"%s\"" % sp[1]
        else:
            q4=" and f.description like \"%%%s%%\"" % query
    
    q="%s from external_files f %s where f.study_id=%s %s %s" % (q1,q2,study,q4,q3)
    return q

def add_meta_from_DICOM():
    print """<!DOCTYPE html>"""
    print
    study_id = form.getfirst('study_id','')
    key = form.getfirst('key','')
    c.execute("select f.id,l.parameters,f.path from external_files f left join external_location l on l.id=f.location where f.study_id=%s", (study_id) )
    st=c.fetchall();
    for s in st:
        try:
            f="%s/%s" % (s[1],s[2])
            dcm=dicom.read_file(f)
            h=dcm[eval("(%s)" % key)]        
            c.execute("select count(*) from external_meta_info where file_id=%s and name=%s", (s[0],h.name))
           
            if int(c.fetchone()[0])>0:
                print "<pre>skipping %s</pre>" % f
            else:
                print "<pre>adding %s</pre>" % f
                
                q = "insert into external_meta_info (study_id,file_id,name,value) values (0,%s,%s,%s)"
                v = (s[0],h.name,h.value)  
                c.execute(q,v)
        except:
            print "<pre>   skipped, not a DICOM</pre>"    
     

    print "</pre>"
    print "back: <a href=metaquery.py?menu=show_study_files&study=%s>here</a><br>" % study_id
   
    
     
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
        q="""select s.name,s.description,s.id from studies s 
                LEFT JOIN modality_ids m ON m.id=s.modality 
                LEFT JOIN study_ids t on s.type_id=t.id
                LEFT JOIN external_meta_info me on me.study_id=s.id
                where s.description like "%%%s%%" 
                    or s.name like "%%%s%%"
                    or m.name like "%%%s%%"
                    or t.name like "%%%s%%"
                    or me.name like "%%%s%%"  
                    or me.value like "%%%s%%"
                    or s.comments like "%%%s%%"
                GROUP BY s.id
        """
        c.execute(q % (query,query,query,query,query,query,query))
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
        q="""select f.study_id,l.parameters,f.path,f.description,t.name from external_files f 
                        LEFT JOIN content_types t ON f.content_type=t.id 
                        LEFT JOIN external_location l on l.id=f.location
                        LEFT JOIN external_meta_info m on f.id=m.file_id
                        where f.description like "%%%s%%" 
                            or f.path like "%%%s%%"  
                            or t.name like "%%%s%%"  
                            or m.name like "%%%s%%"  
                            or m.value like "%%%s%%"  
                            %s 
                            order by f.study_id
                        """
                            
        #print "<pre>%s</pre>" % (q % (query,query,query,query,query,group))
        c.execute(q % (query,query,query,query,query,group))
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
        
    
def edit_study():
    print """<!DOCTYPE html>"""
    print
    
    
    study = form.getfirst('study','')
    name  = form.getfirst('name','')
    description  = form.getfirst('description','')
    MRN  = form.getfirst('MRN','') 
    modality  = form.getfirst('modality','')
    type  = form.getfirst('type','')
    comments  = form.getfirst('comments','')
    print "<A href=metaquery.py?menu=show_study_files&study=%s&group=yes>back</a><br>" % study 
    
    if not name=="":
        c.execute("select * from studies where id=%s", study)
        if len(c.fetchall())==0:
            c.execute("select max(id) from studies");
            study=int(c.fetchone()[0])+1;
            q="insert into studies (Id,name,description,mrn,modality,type_id,comments) values (%s,%s,%s,%s,%s,%s,%s)"
            v=                  (study,name,description,MRN,modality,type,comments)
            print q % v
            c.execute(q,v );
        else:
            c.execute("update studies set name=%s,description=%s,mrn=%s,modality=%s,type_id=%s,comments=%s where id=%s", (name,description,MRN,modality,type,comments,study)); 
      
    if study=="":
        c.execute("select max(id) from studies");
        study=int(c.fetchone()[0])+1;
        st=['','','','','','']        
    else:
        c.execute("select s.name,s.description,s.MRN,s.modality,s.type_id,s.comments from studies s where id=%s",study);
        st=c.fetchone();    


    
    print "<h1>Edit Study:</h1>"
    print "<FORM METHOD=\"push\" action=\"metaquery.py\" method=\"post\">" 
    print "<table>"
    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
    print "<input type=\"hidden\" name=\"menu\" value=\"edit_study\">" 
    print "<tr><td>Name:<td><input size=\"70\" type=\"text\" name=\"name\" value=\"%s\">" % st[0]
    print "<tr><td>Description:<td><input size=\"70\" type=\"text\" name=\"description\" value=\"%s\">" % st[1]
    print "<tr><td>MRN:<td><input size=\"70\" type=\"text\" name=\"MRN\" value=\"%s\">" % st[2]
    print "<tr><td>Modality:<td>%s" % make_option_pulldown("modality","modality_ids",fields="name",select=st[3])
    print "<tr><td>Study Type:<td>%s" % make_option_pulldown("type","study_ids",fields="name",select=st[4])
    
    print "<tr><td valign=top>Comments:<td><textarea name=\"comments\" cols=\"150\" rows=\"30\">%s</textarea>" % st[5]
    print '<tr><td><td><input type="submit" value="Update"></table></FORM>'
    print "</table></form>"
    print "</body>"
    print "</html>"


def update_meta_value():
    print """<!DOCTYPE html>"""
    print
    id = form.getfirst('id','')
    value  = form.getfirst('value','')
    c.execute("update external_meta_info set value=%s where id=%s",(value,id))
    print value

def delete_meta_value():
    print """<!DOCTYPE html>"""
    print
    id = form.getfirst('id','')
    c.execute("delete from external_meta_info where id=%s",(id))
    print "ok"

    

def add_meta_value_to_study():
    print """<!DOCTYPE html>"""
    print
    study_id = form.getfirst('study_id','')
    name  = form.getfirst('name','')
    value  = form.getfirst('value','')
    c.execute("insert into external_meta_info (study_id,name,value) values (%s,%s,%s)",(study_id,name,value))
    print "ok"
            
        
def show_study_files():
    print """<!DOCTYPE html>"""
    print
    print "<html>"
    print """<head>
<script>
function edit_study_meta(i)
{
    val=document.getElementById("study_meta_"+i.toString()).innerHTML;
    document.getElementById("study_meta_"+i.toString()).innerHTML="<input id=\\"study_meta_input_"+i+"\\" type=\\"text\\" id=\\"edit_study_meta_"+i.toString()+"\\" value=\\""+val+"\\">";
    document.getElementById("study_meta_button_"+i.toString()).innerHTML="<button type=\\"button\\" onclick=\\"update_study_meta("+i+")\\">update</button>";
   
}
</script>
<script>
function add_study_meta()
{
    name=document.getElementById("new_study_meta_name").value;
    value=document.getElementById("new_study_meta_value").value;
    study_id=document.getElementById("new_study_meta_id").value;
    
var xmlhttp;
if (window.XMLHttpRequest)
  {// code for IE7+, Firefox, Chrome, Opera, Safari
  xmlhttp=new XMLHttpRequest();
  }
else
  {// code for IE6, IE5
  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
xmlhttp.onreadystatechange=function()
  {
  if (xmlhttp.readyState==4 && xmlhttp.status==200)
    {
        window.location.reload();
    }
  }
  
xmlhttp.open("GET","metaquery.py?menu=add_meta_value_to_study&study_id="+study_id+"&name="+encodeURIComponent(name)+"&value="+encodeURIComponent(value),true);
xmlhttp.send();
}
</script>
<script>
function delete_study_meta(id)
{
    
var xmlhttp;
if (window.XMLHttpRequest)
  {// code for IE7+, Firefox, Chrome, Opera, Safari
  xmlhttp=new XMLHttpRequest();
  }
else
  {// code for IE6, IE5
  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
xmlhttp.onreadystatechange=function()
  {
  if (xmlhttp.readyState==4 && xmlhttp.status==200)
    {
        window.location.reload();
    }
  }
  
xmlhttp.open("GET","metaquery.py?menu=delete_meta_value&id="+id,true);
xmlhttp.send();
}
</script>
<script>
function update_study_meta(i)
{
    str=document.getElementById("study_meta_input_"+i).value;
    id=document.getElementById("study_meta_id_"+i).value;
    
var xmlhttp;
if (window.XMLHttpRequest)
  {// code for IE7+, Firefox, Chrome, Opera, Safari
  xmlhttp=new XMLHttpRequest();
  }
else
  {// code for IE6, IE5
  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
xmlhttp.onreadystatechange=function()
  {
  if (xmlhttp.readyState==4 && xmlhttp.status==200)
    {
        document.getElementById("study_meta_"+i.toString()).innerHTML=xmlhttp.responseText;
        document.getElementById("study_meta_button_"+i.toString()).innerHTML="<button type=\\"button\\" onclick=\\"edit_study_meta("+i+",this.value)\\">edit</button>";  
    }
  }
  
xmlhttp.open("GET","metaquery.py?menu=update_meta_value&id="+id+"&value="+encodeURIComponent(str),true);
xmlhttp.send();
}
</script>
</head>
<body>
"""
    study = form.getfirst('study','')
    grp = form.getfirst('group','')
    query = form.getfirst('query','')
    
    c.execute("select s.name,s.description,s.id,s.mrn,m.name,t.name,s.comments from studies s LEFT JOIN modality_ids m ON m.id=s.modality LEFT JOIN study_ids t on s.type_id=t.id where s.id=%s" % (study) )
    st=c.fetchone();
    print "<A href=metaquery.py>New search</A><br><br>"
    
    print "<table border=0><tr><td valign=top>"
    print "<h2>Study:</h2>"
    print "<table bgcolor=gray>"
    print "<tr bgcolor=white><td><b>ID:</b><td>%s" % st[2] 
    print "<tr bgcolor=white><td><b>Name:</b><td>%s" % st[0]
    print "<tr bgcolor=white><td><b>Description:</b><td>%s" % st[1]
    print "<tr bgcolor=white><td><b>MRN:</b><td>%s" % st[3]
    print "<tr bgcolor=white><td><b>Modality:</b><td>%s" % st[4]
    print "<tr bgcolor=white><td><b>Study type:</b><td>%s" % st[5]
    print "<tr bgcolor=white><td valign=top><b>Comments:</b><td><pre>%s</pre>" % st[6]
    print "</table>"
    print "<A href=metaquery.py?menu=edit_study&study=%s>edit</a><br><br>" % study
    print "<td valign=top>"
    print "<h2>Meta Data:</h2>"
    c.execute("select m.name,m.value,m.id from external_meta_info m where m.study_id=%s" % (study) )
    st=c.fetchall();
    print "<table bgcolor=gray>"
    i=0;
    for e in st:
        i+=1;
        print '<tr bgcolor=white><td>%s<td><div id="study_meta_%i">%s</div><td><div id="study_meta_button_%i"><button type="button" onclick="edit_study_meta(%i)">edit</button></div><div><input type="hidden" id="study_meta_id_%i" value="%s"></div>' % (e[0],i,e[1],i,i,i,e[2])
        print '<td><button type="button" onclick="delete_study_meta(%s)">del</button>' % e[2]
    print '<tr bgcolor=white><td><input id="new_study_meta_name" type="text">'
    print '<td><input id="new_study_meta_value" type="text">'
    print '<input id="new_study_meta_id" type="hidden" value=%s>' % study
    print '<td><button type="button" onclick="add_study_meta()">add</button><td>'
    print "</table>"
    print "<h3>Auto routing:</h3>"
    print """Use for example
    <table bgcolor=gray><tr bgcolor=white><td>route:0x18x0x1030<td>=~.*text.*
    <tr bgcolor=white><td>route:0x18x0x103e:and<td>=~.*other text.*
    </table>
    to automatically route images to this study.<br>Use for example:
     <table bgcolor=gray><tr bgcolor=white><td>addtag:<td>0x10,0x20
    </table>    
    to automatically add DICOM tags to the meta data when automatically routed to this study.
    """
    
    print "</table>"    
    
    print "<h2>Tools:</h2>"
    
    print "<table bgcolor=gray><tr><td>"
    print "<tr bgcolor=white><td>"
    # Create table
    print "<FORM METHOD=\"push\" action=\"metaquery.py\" target=_blank>" 
    print "<table>"
    print "<input type=\"hidden\" name=\"menu\" value=meta_query>"
    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
    print '<td><input type="submit" value="create meta table"></table></FORM>'
    
    print "<td>"
    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<input type=\"hidden\" name=\"menu\" value=add_meta_from_DICOM>"
    print "<input type=\"hidden\" name=\"study_id\" value=%s>" % study
    print "<input type=\"input\" name=\"key\">" 
    print '<input type="submit" value="add DICOM tag to meta data"></FORM> use hex notation e.g. 0x10,0x10 for patient name'
    print "</table>"
    
    print "<h2>Transfer files:</h2>"
    # Send to DICOM node
    print "<table bgcolor=gray><tr><td>"
    print "<tr bgcolor=white><td>"
    
    c.execute("select id,name from dicom_destinations");
    nodes=c.fetchall();    

    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<input type=\"hidden\" name=\"menu\" value=send_to_dicom_node>"
    print "<input type=\"hidden\" name=\"study\" value=\"%s\">" % study
    print "<input type=\"hidden\" name=\"query\" value=\"%s\">" % query
    print "<table><tr><td>Send to DICOM node:"
    print "<td><select name=\"dicom_node\">"
    print "<option value=\"\" checked>-- select DICOM node --"
    for node in nodes:
        print "<option value=\"%i\">%s" % (node[0],node[1])
    print "</select>"
    print '<td><input type="submit" value="Go"></FORM>'
    print "</table>"

    # Move files to different study
    print "<td>"
    
    c.execute("select id,name from studies");
    studies=c.fetchall();    

    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<input type=\"hidden\" name=\"menu\" value=add_to_study>"
    print "<input type=\"hidden\" name=\"old_study_id\" value=\"%s\">" % study
    print "<input type=\"hidden\" name=\"query\" value=\"%s\">" % query
    print "<table><tr><td>move to different study:"
    print "<td><select name=\"study_id\">"
    print "<option value=\"\" checked>-- select Study --"
    for s in studies:
        print "<option value=\"%i\">%s" % (s[0],s[1])
    print "</select>"
    print '<td><input type="submit" value="Go"></FORM>'
    print "</table></table>"
    

    # Search within study
    print "<h2>Search within study:</h1> "
    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<table>"
    print "<input type=\"hidden\" name=\"menu\" value=show_study_files>"
    print "<input type=\"hidden\" name=\"group\" value=yes>" 
    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
    print "<table>"   
    print "<tr><td><input type=\"text\" name=\"query\" value=\"%s\">" % query
    print '<td><input type="submit" value="Go"></table></FORM>'
    print 'You can seatch for descriptions by typing a serach phrase, or search for meta data by typing e.g. Station Name=CT7'
    
    print "<h2>Grouping:</h1> "
    print "<FORM METHOD=\"push\" action=\"metaquery.py\">" 
    print "<input type=\"hidden\" name=\"menu\" value=show_study_files>"
    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
    print "<input type=\"hidden\" name=\"query\" value=\"%s\">" % query

    print "<select name=\"group\">"
    c.execute("select m.name from external_files f join external_meta_info m on m.file_id=f.id where f.study_id=%s group by m.name" , study)
    print "<option value=\"\">all files"
    print "<option value=\"yes\">file description"
    for key in c.fetchall():
        if grp==key[0]:
            print "<option selected value=\"%s\">%s" % ( key[0],key[0])
        else:
            print "<option value=\"%s\">%s" % ( key[0],key[0])
            
    print "</select>"    
    print '<input type="submit" value="Group Files"></FORM>'
    
    q = get_meta_query(study,query,grp);
    #print "<pre>%s</pre>" % q 
    c.execute(q)
    files=c.fetchall();

    N=min(20,len(files))  
    print "<h2>Results:</h2>";
    print "showing %i / %i" % (N,len(files))
    print "<table bgcolor=white>"
    print "<tr bgcolor=#DDDDDD><th>Count<th>File name<th>Description<th>Type<th>Access restrictions<th>Thumbnail" 
    i=0;
    for f in files[0:N]: 
        i=i+1;         
        print "<tr  bgcolor=#EEEEEE><td>{0}<td>{1}/{2:100}<br>file_id={6:50}<td>{3:50}<td>{4:40}<td>{5:40}".format("%i" % (f[8]),f[1],f[2],f[3],f[4],f[5],f[6])
        if float(f[7])==2:
            print "<td><A href=\"http:metaquery.py?menu=getDICOMImage&file_id=%s&pform=PNG\"><image src=\"http:metaquery.py?menu=getDICOMImage&file_id=%s&pform=PNG&size=100\"></A>"% (f[6],f[6])
        print "<tr><td colspan=4><a href=http://10.115.10.160/cgi-bin/analyse_phantom.sh?%s>Run phantom analysis</a>" % urllib.urlencode({'menu':'make_report','dbfile':str(f[6])})    
        c.execute("select name,value,id from external_meta_info where file_id=%s" % (f[6]))
        res=c.fetchall();
        if len(res)>0:
            print "<tr><td colspan=4><table>"
            
            for e in res:
                if e[1].startswith('http:'):
                    print "<tr><td>&nbsp;<td>%s=<A href=\"%s\">%s</A>" % (e[0],e[1],e[1])
                else:
                    print "<tr><td>"
                    print "<table><tr><td><FORM METHOD=\"push\" action=\"metaquery.py\">" 
                    print "<input type=\"hidden\" name=\"menu\" value=show_study_files>"
                    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
                    print "<input type=\"hidden\" name=\"query\" value=\"%s\">" % query
                    print "<input type=\"hidden\" name=\"group\" value=\"%s\">" % (e[0]) 
                    print '<input type="submit" value="Group"></FORM>'
                    print "<td><FORM METHOD=\"push\" action=\"metaquery.py\">" 
                    print "<input type=\"hidden\" name=\"menu\" value=show_study_files>"
                    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
                    print "<input type=\"hidden\" name=\"group\" value=\"%s\">" % grp
                    print "<input type=\"hidden\" name=\"query\" value=\"%s=%s\">" % (e[0],e[1]) 
                    print '<input type="submit" value="filter"></FORM>'
                    print "<td><FORM METHOD=\"push\" action=\"metaquery.py\" target=\"_blank\">" 
                    print "<input type=\"hidden\" name=\"menu\" value=meta_query>"
                    print "<input type=\"hidden\" name=\"study\" value=%s>" % study
                    print "<input type=\"hidden\" name=\"order\" value=\"0\">" 
                    print "<input type=\"hidden\" name=\"meta\" value=\"*Series Date\">" 
                    print "<input type=\"hidden\" name=\"meta\" value=\"%s\">" % query 
                    print "<input type=\"hidden\" name=\"meta\" value=\"%s\">" % e[0] 
                    print "<input type=\"hidden\" name=\"pform\" value=\"html\">" 
                    print '<input type="submit" value="table"></FORM>'
                    print "</table>";
                    
                
                    print "<td>%s=%s" % (e[0],e[1])           
            print "</table>"

            
    print "</table>"
    if N<len(files):
        print "<b>!!! More results are supressed.!!!</b>"                  

def get_study_list():
    c.execute("select id,name,description from studies")
    print    
    for e in c.fetchall():
        print e[1]
        
        
def make_option_pulldown(name,table,fields="name",select=-1):
    c.execute("select id,%s from %s"  % (fields,table))
    out="<select name=%s>\n" % name
    for e in c.fetchall():
        if e[0]==select:
            out+= "<option value=\"%s\" selected>%s</option>\n" % (e[0],e[1])
        else:
            out+= "<option value=\"%s\">%s</option>\n" % (e[0],e[1])
    out+="</select>"

    return out    
    
form = cgi.FieldStorage()       
pform = form.getfirst('pform','html')

if pform=="html" or pform=="edit":
    print "Content-Type: text/html"
    print 
    
try: 
    menu=""
    revision="$Revision: 1 $"
    revision=str.replace(revision,"$Revision: ","");
    revision=str.replace(revision," $","");

    now=datetime.datetime.utcnow()
    
  
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
    elif menu == "edit_study":
        edit_study()   
    elif menu == "DICOM_in_box":
        DICOM_in_box()   
    elif menu == "add_to_study":
        add_to_study()   
    elif menu == "add_meta_from_DICOM":    
        add_meta_from_DICOM() 
    elif menu == "meta_query":    
        meta_query()    
    elif menu == "getDICOMImage":  
        getDICOMImage()
    elif menu == "update_meta_value":
        update_meta_value()
    elif menu == "send_to_dicom_node":
        send_to_dicom_node()
    elif menu == "add_meta_value_to_study":
        add_meta_value_to_study()
    elif menu == "delete_meta_value":
        delete_meta_value()
        
    else:
        print "unknown menu selection"
    
except:
    raise
    