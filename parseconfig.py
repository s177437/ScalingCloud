'''
Created on 7. apr. 2015

@author: stianstrom

'''
import ConfigParser
class Hammer : 
    username=""
    password=""
    def setUserName(self,user):
        self.username=user
    def getUserName(self):
        return self.username
    def setPassword(self, pw):
        self.password=pw
    def getPassword(self):
        return self.password
class Nova : 
    username=""
    password=""
    url=""
    flavor=0
    imageid=""
    nicid=""
    key=""
    tenant=""
    emailaddress=""
    emailpassword=""
    emailusername=""
    emailserver=""
    def setUserName(self,user):
        self.username=user
    def getUserName(self):
        return self.username
    def setPassword(self, pw):
        self.password=pw
    def getPassword(self):
        return self.password
    def setUrl(self, u):
        self.url=u
    def getUrl(self):
        return self.url
    def getFlavor(self):
        return self.flavor
    def set_flavor(self, f):
        self.flavor = f
    def getImageid(self):
        return self.imageid
    def setImageId(self, i):
        self.imageid=i
    def getNicId(self):
        return self.nicid
    def setNicId(self, i):
        self.nicid=i 
    def getKey(self):
        return self.key
    def setKey(self,k):
        self.key=k    
    def setTenant(self,t):
        self.tenant=t 
    def getTenant(self):
        return self.tenant  
    def getEmailAddress(self):
        return self.emailaddress
    def setEmailAddress(self,e):
        self.emailaddress=e
    def getEmailPassword(self): 
        return self.emailpassword
    def setEmailPassword(self, p):
        self.emailpassword=p
    def setEmailUsername(self, u):
        self.emailusername=u
    def getEmailUsername(self):
        return self.emailusername
    def setEmailSMTPServer(self, s):  
        self.emailserver=s 
    def getEmailSMTPServer(self):
        return self.emailserver   


        






