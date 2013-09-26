import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Date;
import java.util.ArrayList;
import java.util.HashMap;

public class meta_db {
    
    private Connection c = null;
    private Statement  s = null;
    private String     sep ="/";
    private Location[] loc;
    
    /**
     *Constructor
     */
    public meta_db() throws java.lang.Exception {
        Config cf=new Config("/etc/metadbconfig.cfg"); // Read config file /etc/
        Class.forName("com.mysql.jdbc.Driver");
        String URI="jdbc:mysql://";
        URI=URI+cf.getProperty("mysql_server");
        URI=URI+"/"+cf.getProperty("mysql_db");
        URI=URI+"?user="+cf.getProperty("mysql_user");
        URI=URI+"&password="+cf.getProperty("mysql_password");
        c = DriverManager.getConnection(URI);
        s = c.createStatement();
        readLocations();
    }
    
    /**
     * directory separator
     */
    public void setDirSep(String dir_sep){ sep = dir_sep; }
 
   /**
    *Search database for Study descriptons.
    *Returns list of ids.
    */
    public int[] searchStudies(String st,String meta) throws java.sql.SQLException {
        String[] meta_data=meta.split("=");
        String q;
        if (meta_data.length<2) {
            q="select id,name from studies where name like \""+st+"\"";
        } else {
            q="select s.id,s.name from studies s ";
            q+=" join external_meta_info m on m.study_id=s.id and m.name=\""+meta_data[0]+"\" and m.value like \""+meta_data[1]+"\""; 
            q+=" where s.name like \""+st+"\"";
        }
        ResultSet res = s.executeQuery(q);
        // System.out.println(q);
        ArrayList al = new ArrayList();
        while (res.next()) {
            Integer id=new Integer(res.getInt("id"));
            String name = res.getString("name");
            al.add(id);
            // System.out.println(id+"\t"+name);
        }
        int[] ret=new int[al.size()];
        for(int i=0;i<ret.length;i++){
            ret[i]=((Integer)al.get(i)).intValue();
        }
        return ret;
    }

    /**
     *Search File descriptions.
     */
    public String[] searchFiles(String study,String meta_study,String description, String meta) throws java.sql.SQLException {
        int[] st = searchStudies(study,meta_study);
        return searchFiles(st[0],description,meta);
    }
    
    /**
     *Search File descriptions
     */
    public String[] searchFileDescription(int study_id,String description,String meta) throws java.sql.SQLException {
        String q; 
        String[] meta_data=meta.split("=");
        if (meta_data.length<2) {
            q="select f.description from external_files f ";
        } else {
            q="select f.description from external_files f ";
            q+=" join external_meta_info m on m.file_id=f.id and m.name=\""+meta_data[0]+"\" and m.value like \""+meta_data[1]+"\""; 
        }
        q+="where f.study_id="+ study_id +" and f.description like \""+description+"\" ";
        q+="group by f.description";
        
        ResultSet res = s.executeQuery(q); 
        ArrayList al = new ArrayList();
        while (res.next()) {
            String v=res.getString("description");
            al.add(v);
            // System.out.println(id+"\t"+name);
        }
        return (String[])( al.toArray(new String[0]) );
    }
    
    /**
     * Search Meta information
     * Returns all values of a given meta name that matches a particular file description
     */
    
    public String[] searchFileMeta(int study_id,String description,String meta_name) throws java.sql.SQLException {
        String q; 
        q="select m.value from external_files f join external_meta_info m on m.file_id=f.id and m.name=\""+meta_name+"\"";
        q+="where f.study_id="+ study_id +" and f.description like \""+description+"\" ";
        q+="group by m.value";
        ResultSet res = s.executeQuery(q); 
        ArrayList al = new ArrayList();
        while (res.next()) {
            String v=res.getString("value");
            al.add(v);
            // System.out.println(id+"\t"+name);
        }
        return (String[])( al.toArray(new String[0]) );
    }        
    
    /**
     *Search File descriptions
     */
    public String[] searchFiles(int study_id,String description, String meta) throws java.sql.SQLException {
        String[] meta_data=meta.split("=");
        
        String q;
        if (meta_data.length<2) {
            q="select l.parameters,f.path from external_files f join external_location l on l.id=f.location where f.study_id="+ study_id +" and f.description like \""+description+"\" ";
        } else {
           q="select l.parameters,f.path from external_files f join external_location l on l.id=f.location left join external_meta_info m on m.file_id=f.id where f.study_id="+ study_id +" and f.description like \""+description+"\" and m.name=\""+meta_data[0]+"\" and m.value like \""+meta_data[1]+"\" ";
           // System.out.println(q);
        }
        q+="group by f.id";
        
        ResultSet res = s.executeQuery(q); 
        ArrayList al = new ArrayList();
        while (res.next()) {
            String l=res.getString("parameters");
            String p=res.getString("path");
            al.add(l+sep+p);
            // System.out.println(id+"\t"+name);
        }
        return (String[])( al.toArray(new String[0]) );
    }
    
      
    /** 
     * read location paths from db
     */
    private void readLocations() throws java.sql.SQLException {
       String q="select id,parameters from external_location where type=\"local\"";
       ResultSet res = s.executeQuery(q);
       ArrayList li = new ArrayList();
       while(res.next()){ li.add(new Location(res.getInt("id"),res.getString("parameters")));}
       loc = (Location[])(li.toArray(new Location[0]));
    }
    
    /**
     *Find location id from data base given a path
     */
    public Location findLocation(String path) throws AssertionError {
        Location j=null;
        for (int i=0;i<loc.length;i++){
            if (path.startsWith(loc[i].path)) {
                if(j==null){ j = loc[i]; } 
                else { throw(new AssertionError("more than one path matches in db. Correct data base.")); }
            }
        }
        return j;
    }
    
    /** 
     * Split file path in directories and file name
     */
    
    private String[] SplitPath(String name){
        String[] p=name.split(sep);
        StringBuilder path= new StringBuilder();
        for(int j=0;j<p.length-1; j++){
            path.append(p[j]);
            path.append(sep);
        }
        String[] out= new String[2];
        out[0]=path.toString();
        out[1]=p[p.length-1];
        return out;
    }
        
        
    /**
     *get meta info with for all files in files. Name: Name of the meta info field.
     */
    public String[] getMeta(String[] files,String name) throws java.sql.SQLException{
        String lastpath=new String("");
        Location lo=null;
        String[] ret = new String[files.length];
        
        for (int i=0; i<files.length; i++){
            String[] p = SplitPath(files[i]);
            if (!p[0].equals(lastpath)){
                lastpath=p[0].toString();
                lo = findLocation(lastpath);
            }
            if (lo==null){ new AssertionError("File location not in location data base. Correct data base."); }
            String q="select m.name,m.value,m.id from external_meta_info m left join external_files f on f.id=m.file_id where f.path=\""+lo.strip(files[i])+"\" and m.name=\""+name+"\" and f.location="+lo.id;
            // System.out.println(q);
            ResultSet res = s.executeQuery(q);
            if (res.first()) {
                ret[i] = res.getString("value");
            }
            // System.out.println(name+"="+ret[i]);
        }
            
        return ret;
    }
    
    
    /**
     *Save Meta information in db
    */
    public void saveMeta(String[] files,String name,String[] values) throws java.sql.SQLException{
        String lastpath=new String("");
        Location lo=null;
        String[] ret = new String[files.length];
        
        for (int i=0; i<files.length; i++){
            String[] p = SplitPath(files[i]);
            if (!p[0].equals(lastpath)){
                lastpath=p[0].toString();
                lo = findLocation(lastpath);
            }
            if (lo==null){ new AssertionError("File location not in location data base. Correct data base."); }
            String q="select f.id from external_files f where f.path=\""+lo.strip(files[i])+"\" and f.location="+lo.id;
            // System.out.println(q);
            ResultSet res = s.executeQuery(q);
            res.first();
            int id=res.getInt("Id");
            q="insert into external_meta_info (file_id,name,value) values ("+id+",\""+name+"\",\""+values[i]+"\")";
            s.executeUpdate(q);
        }
    }  
    
    /**
     *Delete Meta information in db
    */
    public void deleteMeta(String[] files,String name) throws java.sql.SQLException{
        String lastpath=new String("");
        Location lo=null;
        String[] ret = new String[files.length];
        
        for (int i=0; i<files.length; i++){
            String[] p = SplitPath(files[i]);
            if (!p[0].equals(lastpath)){
                lastpath=p[0].toString();
                lo = findLocation(lastpath);
            }
            if (lo==null){ new AssertionError("File location not in location data base. Correct data base."); }
            String q="select f.id from external_files f where f.path=\""+lo.strip(files[i])+"\" and f.location="+lo.id;
            // System.out.println(q);
            ResultSet res = s.executeQuery(q);
            res.first();
            int id=res.getInt("Id");
            q="delete from external_meta_info where file_id="+id+" and name=\""+name+"\" ";
            s.executeUpdate(q);
        }
    }   
    
    /**
     *Move file to different study
    */
    public void moveFiles(String[] files,int study) throws java.sql.SQLException{
        String lastpath=new String("");
        Location lo=null;
        String[] ret = new String[files.length];
        
        for (int i=0; i<files.length; i++){
            String[] p = SplitPath(files[i]);
            if (!p[0].equals(lastpath)){
                lastpath=p[0].toString();
                lo = findLocation(lastpath);
            }
            if (lo==null){ new AssertionError("File location not in location data base. Correct data base."); }
            String q="select f.id from external_files f where f.path=\""+lo.strip(files[i])+"\" and f.location="+lo.id;
            // System.out.println(q);
            ResultSet res = s.executeQuery(q);
            res.first();
            int id=res.getInt("Id");
            q="update external_files f set f.study_id="+study+" where id="+id;
            s.executeUpdate(q);
        }
    }      
    
    /**
     * Add Study Meta Data
     */
    public void addStudyMeta(int study_id,String name,String value) throws java.sql.SQLException{
        String q="insert into external_meta_info (study_id,name,value) values ("+study_id+",\""+name+"\",\""+value+"\")";
        s.executeUpdate(q);
    }     
    
    /**
     * Delete Study Meta Data
     */
    public void deleteStudyMeta(int study_id,String name,String value) throws java.sql.SQLException{
        String q="delete from external_meta_info where study_id="+study_id+" and name=\""+name+"\" and value=\""+value+"\" ";
        s.executeUpdate(q);
    }     
    
   /**
    *Print out all Study descriptions
    */
    public void printStudies() throws java.sql.SQLException {
        ResultSet res = s.executeQuery("select * from studies");
        while (res.next()) {
            int    id   = res.getInt("id");
            String name = res.getString("name");
            System.out.println(id+"\t"+name);
        }
    }
    
 
    /**
     *Close db connection
     */
    public void close() {
        try {
            if (s != null) { s.close();}
            if (c != null) { c.close();}
        } catch (Exception e) {
            
        }
    }
    
    /**
     *Class for file locations in data basae
     */
    public class Location {
        public int id;
        public String path;
        
        /**
         *Locations in the database have an id and a path
         */
        public Location(int id_,String path_){ id=id_; path=path_;}
        /** 
         * Strip location path from path
         */
        public String strip(String path_){
            String ret = null;
            // System.out.println("("+path+") "+path_.substring(0,path.length()));
            if (path_.substring(0,path.length()).equals(path)){
                ret=path_.substring(path.length()+1,path_.length());
            }
            return ret;
        }
            
    }
    
}