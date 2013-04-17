/**
* Read config file modified from 
* http://www.opencodez.com/java/read-config-file-in-java.htm
* Posted on July 11, 2009 by Pavan
*/


import java.util.*;
import java.util.Properties;
import java.io.FileInputStream;
 
public class Config
{
   Properties configFile;
   public Config(String filename)
   {
    configFile = new java.util.Properties();
    try {
      configFile.load(new FileInputStream(filename));
    }catch(Exception eta){
        eta.printStackTrace();
    }
   }
 
   public String getProperty(String key)
   {
    String value = this.configFile.getProperty(key);
    return value;
   }
}