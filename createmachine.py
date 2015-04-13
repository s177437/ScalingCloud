import matplotlib
matplotlib.use('Agg')
import subprocess
import StringIO
import email
import smtplib
import mimetypes
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEBase import MIMEBase
from email import encoders
import time
from novaclient import client
import ConfigParser
import matplotlib.pyplot as plt
import logging
from parseconfig import *
class MachineTasks : 
    hostlist=[]
    hammer=Hammer()
    nova=Nova()
    hammerusername=""
    hammerpassword=""
    novausername=""
    novapassword=""
    image=""
    flavor=0
    tenant=""
    url=""
    nic=""
    key=""
    emailaddress=""
    emailpassword=""
    emailserver=""
    emailusername=""
    logging.basicConfig(filename='/var/log/scaling.log',level=logging.DEBUG)
    def initializeAndFetch(self):
        config=ConfigParser.SafeConfigParser()
        config.read("config.ini")
        self.hammer.setUserName(config.get('Hammer','hammerusername'))
        self.hammer.setPassword(config.get('Hammer','hammerpassword'))
        self.nova.setUserName(config.get('Nova', 'novausername'))
        self.nova.setPassword(config.get('Nova','novapassword'))
        self.nova.setUrl(config.get('Nova','url'))
        self.nova.setKey(config.get('Nova',"keyname"))
        self.nova.setNicId(config.get('Nova','nicid'))
        self.nova.setImageId(config.get('Nova','imageid'))
        self.nova.set_flavor(config.get('Nova','flavor'))
        self.nova.setTenant(config.get('Nova','tenant'))
        self.nova.setEmailAddress(config.get('Nova','emailaddress'))
        self.nova.setEmailPassword(config.get('Nova','emailpassword'))
        self.nova.setEmailSMTPServer(config.get('Nova','mailserver'))
        self.nova.setEmailUsername(config.get('Nova','mailusername'))
        self.hammerusername=self.hammer.getUserName()
        self.hammerpassword=self.hammer.getPassword()
        self.novausername=self.nova.getUserName()
        self.novapassword=self.nova.getPassword()
        self.flavor=self.nova.getFlavor()
        self.url=self.nova.getUrl()
        self.nic=self.nova.getNicId()
        self.key=self.nova.getKey()
        self.image=self.nova.getImageid() 
        self.tenant=self.nova.getTenant()
        self.emailaddress=self.nova.getEmailAddress()
        self.emailpassword=self.nova.getEmailPassword()
        self.emailserver=self.nova.getEmailSMTPServer()
        self.emailusername=self.nova.getEmailUsername()
        
        
    def __init__(self):
        self.hostlist=[]
    def authenticate(self):
	nova = client.Client(2, self.novausername, self.novapassword, self.tenant, self.url)
        return nova
    def getcommandoutput(self, command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, error) = p.communicate()
        return output
    def runcommand(self, command):
        subprocess.call(command, shell=True)
    def readUserData(self, name):
        file=open(name,'r')
        content= file.readlines()
        fulltext=""
        for line in content :
                fulltext+=line
        return fulltext
    def getPerformancePercent(self) :
            number = 0.00
            numberlist = []
            for ip in self.hostlist :
    		number = int((self.getcommandoutput("ssh  -o StrictHostKeyChecking=no  ubuntu@" + ip + " 'netstat -nat | grep " + ip + ":80| wc -l'")))
                if number > 10 :
                        logging.warning("Host: "+ ip+ " has more than  "+str(number) + " connections")
                        self.writeNumbersToFile(ip, number)
                numberlist.append(number)
            a = sum(numberlist)
            return a
    def writeNumbersToFile(self,ip, number):
        numberfile = open("reports/"+ip, 'a')
        numberfile.write(str(number) + "\n")
        numberfile.close()
    # This function MUST use the nova command line tool, to deploy machines with custom user data, cannot be changed, in order to deploy machines with commands successfully
    def createMachine(self, name) : 
        self.nova.servers.create(name=name, image=self.image,flavor=self.flavor, nics=[{"net-id":self.nic,"v4-fixed-ip": ''}],key_name=self.key, userdata=self.readUserData("bin/test.txt"))
        #self.runcommand("nova boot --flavor "+ str(self.flavor)+" --image "+self.image+" --nic net-id="+self.nic+" --user-data=test.sh  --key-name "+ self.key +" " + name)
        logging.info("Machine is added, sleeping while waiting for the machine to configure itself")
        time.sleep(150)
        self.addIPtoList(name)
    
    def deleteMachine(self, name): 
        nova = self.authenticate()
        server_list = nova.servers.list()
	deletemachine=None
        for s in server_list: 
            if s.name == name:
                logging.info("Found node " + s.name + " deleting .....")
                deletemachine = s
        nova.servers.delete(deletemachine)
        self.removeIPfromList(name)
        logging.info("Sleeping to let the system reconfigure itself")
        time.sleep(60)
    # Get console output from a given machine
    def checkOutputFromMachine(self, name):
            nova = self.authenticate()
            server_list = nova.servers.list()
            for s in server_list:
                if s.name == name:
                    print nova.servers.get_console_output(s)
    
    def createHostList(self) : 
    	numhosts = int(self.getcommandoutput("nova list | grep webserver | wc -l "))
    	logging.info("There are "+ str(numhosts)+ " hosts at the moment")
    	listofhosts = []
    	hoststring = self.getcommandoutput("nova list | grep webserver | awk '{print $4}'")
    	word = ""
    	for letter in hoststring : 
    		if letter != "\n" : 
    			word += letter
    		else: 
    			listofhosts.append(word)
    			word = " "
    	for hostname in listofhosts : 
    		ip = self.getIP(hostname)
    		self.hostlist.append(str(ip))
    	
    def deleteHostFromForeman(self, hostname) : 
    	self.runcommand("hammer -u "+self.hammerusername+" -p "+self.hammerpassword+" host delete --name " + hostname + ".openstacklocal")	
    def getIP(self,hostname): 
    	ip = self.getcommandoutput("nova list | grep " + hostname + " | awk '{print $12}'|cut -f2 -d '='").strip()
    	return ip
    def addHostToHaProxy(self, hostname) :
        ip = self.getIP(hostname)
	content="" 
        for line in open('/etc/puppet/environments/common/loadbalancer/files/haproxy.cfg','r'): 
		content+=line                    
	if hostname in content:
		logging.info("The server is already added to haproxy config ")
	else : 
                self.runcommand("echo 'server " + hostname + " " + ip + ":80 check' >> /etc/puppet/environments/common/loadbalancer/files/haproxy.cfg")
                    
    def deleteHostFromHaproxy(self, ip):
    	self.runcommand("sed -i '/" + ip + "/d' /etc/puppet/environments/common/loadbalancer/files/haproxy.cfg ")
    
    def deleteHostFromPuppet(self, hostname): 
    	self.runcommand("puppet cert clean " + hostname + ".openstacklocal")
    
    def removeIPfromList(self, hostname):
        ip = self.getIP(hostname)
        self.hostlist.remove(ip)
        logging.info("Removing host from haproxy config")
        self.deleteHostFromHaproxy(hostname)
        logging.info("Removing Puppet certificate")
        self.deleteHostFromPuppet(hostname)
        logging.info("Removing Host from Foreman")
        self.deleteHostFromForeman(hostname) 
    
    def addIPtoList(self, hostname) : 
        ip = self.getIP(hostname)
        self.hostlist.append(ip)
        logging.info("Adding new machine to haproxy config")
        self.addHostToHaProxy(hostname)
        logging.info("Removing old ssh key")
        self.runcommand("ssh-keygen -f '/root/.ssh/known_hosts' -R " + ip)  
    
    def checkPerformance(self):
        machinename = "webserver" + str(len(self.hostlist) + 1)
    	logging.info(machinename)
	hostliststring=''.join(str(self.hostlist))
        logging.info(hostliststring)
    	oktodelete = 0
    	number = 0
        while number < 1000 :
            number = self.getPerformancePercent()
            logging.info(""+str(number))
            self.writeNumbersToFile("stats", number)
            counter = len(self.hostlist)
            if (number > 60 and counter == 2) :
                logging.warning("More than 60 connections")
                self.createMachine(machinename)
                oktodelete = 1
    	    	counter = 3
            elif(number > 700 and counter == 3):	
                machinename = "webserver" + str(len(self.hostlist) + 1)
                logging.warning("700 connections")
                self.createMachine(machinename)
            	oktodelete = 1
            elif(number > 3 and number < 5 and counter > 2) : 	
                self.deleteMachine(machinename)
                oktodelete = 0
                machinename = "webserver" + str(len(self.hostlist))
    	logging.warning("The toal number of connections has reached 100000 ")
    def fetchFiles(self): 
	files=self.getcommandoutput("ls reports/").split()
	return files 
    def readFile(self, filename):
        numberlist = []
        file = open(filename, 'r')
        for number in file : 
            numberlist.append(int(number))
        return numberlist 
    
    def createPlot(self, filename):
        plt.plot(self.readFile(filename))
        plt.ylabel("Number of Connections")
        plt.xlabel("Number of checks")
        plt.savefig(filename + ".pdf")
	plt.close()
    def draw(self):
        files=self.fetchFiles()
        for name in files : 
            self.createPlot("reports/"+name)
        print "Creating zip file"
        self.runcommand("zip reports/graphs.zip reports/*.pdf")
    def deleteGraphsAndData(self):
        print "Flushing data in the reports directory"
        self.runcommand("rm reports/*")
        
    
    def sendGraphsPerEmail(self):
        msg = MIMEMultipart()
        msg['To'] = self.emailaddress
        msg['From'] = self.emailaddress
        msg['Subject'] = "Subject : Stats"
        body = '''
        This mail contains a pdf with graphed results from the dynamic cloud
        Regards 
        Stian
            '''
        msg.attach( MIMEText(body) )
        ctype, encoding = mimetypes.guess_type('graphs.zip')
        print ctype, encoding
        maintype, subtype = ctype.split('/', 1)
        print maintype, subtype
        msg.attach(MIMEText(body))
        part = MIMEBase(maintype, subtype)
        part.set_payload(open('reports/graphs.zip', 'rb').read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename='graphs.zip')
        msg.attach(part)
        server = smtplib.SMTP(self.emailserver)
        server.starttls()
        server.login(self.emailusername, self.emailpassword)
        server.sendmail(self.emailaddress, self.emailaddress, msg.as_string())
        server.quit()
                
    def testPlotsList(self):
        hostlist=self.fetchFiles()
        hostlist.remove("stats")
        numlist=[]
        listoflist=[]
        ydata=[]
        index=0
        for host in hostlist : 
            numlist.append(len(self.readFile("reports/"+host)))
            listoflist.append(self.readFile("reports/"+host))
        xdata=range(0,max(numlist),1)
        maxlength=max(numlist)
        indexlist=[]
        for i in listoflist : 
            if len(i)==maxlength : 
                ydata = i 
                listoflist.remove(i)
                plt.plot(xdata,ydata)
                plt.savefig("reports/allstats.pdf")
        for i in listoflist : 
            xdata=range((maxlength-len(i)),maxlength,1)
            ydata=i
            plt.plot(xdata,ydata)
            plt.savefig("reports/allstats.pdf")	                
