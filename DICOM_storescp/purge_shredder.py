# -*- coding: utf-8 -*-
"""
Created on Tue Aug  7 16:51:12 2012

@author: wstefan@mdanderson.org

A python script to add existing content to the meta database.
Run the script in the directory with the file name as argument.

"""

import MySQLdb,datetime,os,dateutil.parser
import time,os
from optparse import OptionParser
from metadbtools import *

parser = OptionParser()

(options, args) = parser.parse_args()

trash_id=20;

c.execute('select f.id,l.parameters,f.path,count(*) from external_files f join external_location l on l.id=f.location join studies s on s.id=f.study_id join study_ids si on si.id=s.type_id and si.name="shredder" join external_files f1 on f1.location=f.location and f1.path=f.path group by f.id');

for f in c.fetchall():
   fn = "%s/%s" % (f[1],f[2])
   print "%s" % fn
   if os.path.exists("%s" % fn):
      try:
         if f[3]==1:
             os.system("rm %s" % fn);
             print "delete file"
         else: 
             print "remove db entry"
           
         c.execute("delete from external_files where id = %s" % f[0])
         c.execute("delete from external_meta_info where file_id = %s" % f[0])
      except:
         print "delete failed"
   else:
      c.execute("delete from external_files where id = %s" % f[0])
      c.execute("delete from external_meta_info where file_id = %s" % f[0]) 
      print "does not exist. Removed from DB."



