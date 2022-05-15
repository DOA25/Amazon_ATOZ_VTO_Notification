from selenium import webdriver
import time
import json
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
from telegram import Update
from selenium.webdriver.chrome.options import Options
from os.path import exists
import pickle
from urllib.parse import urlparse
import os
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service




class amazonatoz:
    c_options = Options()
    c_options.add_argument("--no-sandbox")
    c_options.add_argument("--headless")
    c_options.add_argument('--log-level=1')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),chrome_options=c_options)
    atoz = "https://atoz.amazon.work/"
    homepage = 'https://atoz.amazon.work/schedule'
    loginPage = "https://idp.amazon.work/idp/enter?sif_profile=amazon-passport"
    opportunitiesURL = 'https://atoz.amazon.work/api/v1/opportunities/get_opportunities?employee_id='
    startLogin = False
    chatID = ""
    otp = ""
    updater = None


    def otpHandle(update: Update, contex: CallbackContext):
        otp = str(update.message.text)
        if otp.isnumeric():
            amazonatoz.otp = otp

    def start(update: Update, contex: CallbackContext):
        amazonatoz.chatID = update.effective_chat.id
        amazonatoz.startLogin = True


    def __init__(self,username,password,updater):
        self.username = username
        self.password = password
        amazonatoz.updater = updater
        self.chatID = ""
        startHandler = CommandHandler('start',amazonatoz.start)

        otpHandler = MessageHandler(Filters.text &(~Filters.command),amazonatoz.otpHandle)
        amazonatoz.updater.dispatcher.add_handler(otpHandler)
        amazonatoz.updater.dispatcher.add_handler(startHandler)
        amazonatoz.updater.start_polling()
        amazonatoz.driver.get(amazonatoz.loginPage)
        while True:
            if amazonatoz.startLogin:
                self.writeToLog("User started the login process")
                self.login()
                break
            self.writeToLog("Waiting for user to send /start")
            time.sleep(5)

        self.workid = self.getWorkID()
        amazonatoz.opportunitiesURL = amazonatoz.opportunitiesURL + self.workid
        self.writeToLog("Work ID = " + self.workid)
        self.saveCookies()
        self.writeToLog("You are now able to get opportunities...")
        self.opportunitiesJSON = {}

    def loadCookies(self):
        amazonatoz.driver.get("https://atoz.amazon.work/404") 
        cookies = pickle.load(open("cookies.pkl","rb"))
        for cookie in cookies:
            amazonatoz.driver.add_cookie(cookie)

    def getChatID(self):
        return amazonatoz.chatID

    def saveCookies(self):
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl","wb"))

    def isLogin(self):
        if amazonatoz.driver.current_url != amazonatoz.homepage or amazonatoz.driver.current_url != amazonatoz.opportunitiesURL:
            return True
        return False

    def login(self):
        print("Logging into ATOZ...")
        amazonatoz.driver.find_element_by_id('login').send_keys(self.username)
        amazonatoz.driver.find_element_by_id('password').send_keys(self.password)
        amazonatoz.driver.find_element_by_id('buttonLogin').click()
        if not "Verify your identity." in self.driver.page_source and not amazonatoz.driver.current_url == amazonatoz.homepage:
            raise ValueError("Login Failed...")
        else:
            self.writeToLog("login successful...")

        if "Verify your identity" in amazonatoz.driver.page_source:
            self.getOTP()
            if not amazonatoz.driver.current_url == amazonatoz.homepage:
                raise ValueError("Unable to complete One time password...")
        else:
            print("Web driver on homepage...")



    def getWorkID(self):
        id = self.driver.find_element_by_xpath("//*[text()='Profile']").get_attribute("href")
        removeid = ''.join(x for x in id if x.isdigit())
        print(id)
        return removeid

    def __UpdateOpportunities(self):
        failed = True
        while failed:
            try:
                amazonatoz.driver.get(amazonatoz.opportunitiesURL)
                amazonatoz.driver.refresh()
                domain = urlparse(amazonatoz.driver.current_url)
                if domain.netloc == "idp.amazon.work":
                    amazonatoz.driver.find_element_by_id('login').send_keys(self.username)
                    amazonatoz.driver.find_element_by_id('password').send_keys(self.password)
                    amazonatoz.driver.find_element_by_id('buttonLogin').click()
                if("vtoOpportunities" in amazonatoz.driver.page_source):
                    opps = self.driver.find_element_by_tag_name('body').text
                    self.opportunitiesJSON = json.loads(opps)
                    failed = False
            except Exception as e :
                self.writeToLog(e)
                continue

                
        
    def refreshPage(self):
        amazonatoz.driver.get(amazonatoz.homepage)
        time.sleep(4)

    def getVTO(self):
        self.__UpdateOpportunities()
        return self.opportunitiesJSON['vtoOpportunities']

    def getVET(self):
        self.__UpdateOpportunities()
        return self.opportunitiesJSON['vetOpportunities']
        

    def getReply(self,msgid):
        old_update = self.TelegramBot.updates
        while old_update == self.TelegramBot.getupdates():
            time.sleep(1)
            self.writeToLog("waiting for response")
        self.writeToLog("response recieved")
        msgs = self.TelegramBot.updates['result']
        otp = str(msgs[len(msgs)-1]['message']['text']).replace(" ","")
        if otp.isnumeric():
            self.TelegramBot.sendRequest(self.TelegramBot.TelegramMethods.SENDMESSAGE,{'chat_id':msgid,'text':"OTP ACCEPTED"})
            return otp
        else:
            self.TelegramBot.sendRequest(self.TelegramBot.TelegramMethods.SENDMESSAGE,{'chat_id':msgid,'text':"Invalid OTP please resend"})
            return self.getReply(msgid)
    
    def writeToLog(self,message):
        logfile = None
        if exists("amazonatozlog.txt"):
            logfile = open("amazonatozlog.txt","a")
        else:
            logfile = open("amazonatozlog.txt","w")
        log = "[{}]{}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"),message)
        print(log)
        logfile.write(log)
        logfile.close()


    def getOTP(self):
        amazonatoz.updater.bot.send_message(chat_id=amazonatoz.chatID, text="Please send one time password...")
        amazonatoz.driver.find_element_by_id('buttonContinue').click()
        self.writeToLog("Grabbing one time password...")
        while (True):
            if amazonatoz.otp != "":
                amazonatoz.driver.find_element_by_id('code').send_keys(amazonatoz.otp)
                amazonatoz.driver.find_element_by_id('trustedDevice').click()
                amazonatoz.driver.find_element_by_id('buttonVerifyIdentity').click()
                amazonatoz.updater.bot.send_message(chat_id=amazonatoz.chatID, text="OTP ACCEPTED...")
                break
            print("Waiting for one time password...")
            time.sleep(5)

    
    
    


