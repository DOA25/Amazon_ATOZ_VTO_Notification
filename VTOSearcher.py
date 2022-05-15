from amazonatoz import amazonatoz as amazon
import logging
from telegram.ext import Updater
from telegram import Update
from telegram import Bot
from telegram.ext import (
    CallbackContext,
    CommandHandler)
import time
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import json




chatId = []
username = "" #Amazon login
password = "" #Amazon password
apikey = "" #Telegram API key
updater = Updater(token=apikey, use_context=True)
dispatcher = updater.dispatcher
isSearchVTOActive = False
atoz = None
checkHeartbeat = False

def sendPhoto(update: Update, context: CallbackContext):
    atoz.driver.save_screenshot('debug.png')
    context.bot.send_photo(atoz.getChatID(),photo=open('debug.png', 'rb'))

def searchVto():
    global checkHeartbeat
    atoz.writeToLog("Searching for VTOS")
    while True:
        try:
            active = 0
            inactive = 0
            vtos = atoz.getVTO() #json.load(open("opjson/get_opportunities.json",'r'))['vtoOpportunities']
            for vto in vtos:
                url = ""
                if vto["active"] or vto["inactive_reason"] == None or checkHeartbeat:
                    if not checkHeartbeat:
                        url = "https://atoz.amazon.work/time/optional/"+vto['opportunity_id']
                        active += 1
                    updater.bot.send_message(chat_id=atoz.getChatID(), text="A VTO has been found. {}".format(url))
                    checkHeartbeat = False
                else:
                    inactive += 1
            print("[{}]No of VTOS: {}({} inactive and {} active)".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"),len(vtos),inactive,active))
            time.sleep(10)
        except Exception as e:
            atoz.writeToLog(e)
            continue

def checkVTOSearcher(update: Update, context: CallbackContext):
    global checkHeartbeat
    atoz.writeToLog("Checking if searchVTO() is working")
    checkHeartbeat = True

def createOppMessage(opp):
    start = opp['start_time_local'].replace("T"," at ")
    end = opp['end_time_local'].replace("T"," at ")
    signup = opp['signup_start_time_local'].replace("T"," at ")
    oppMessage = "Start: "+start+"\n\n"+"End: "+end+"\n\nWorkgroup: "+opp['workgroup']+"\n\nSign up: "+ signup
    if opp["active"] == False:
        oppMessage = oppMessage+"\n\nInactive Reason: "+opp['inactive_reason']
    return oppMessage
    
def vto(update: Update, context: CallbackContext):
    atoz.writeToLog("User has called /vto")
    vtos = atoz.getVTO()
    if len(vtos) != 0:
        for vto in vtos:
            context.bot.send_message(chat_id=atoz.getChatID(), text=createOppMessage(vto))
    else:
        context.bot.send_message(chat_id=atoz.getChatID(), text="There are no VTOS")

def vet(update: Update, context: CallbackContext):
    vets = atoz.getVET()
    if len(vets) != 0:
        for vet in vets:
            context.bot.send_message(chat_id=atoz.getChatID(), text=createOppMessage(vet))
    else:
        context.bot.send_message(chat_id=atoz.getChatID(), text="There are no VETS")


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def main():
    global atoz
    vto_handler = CommandHandler('vto',vto)
    vet_handler = CommandHandler('vet',vet)
    screenshot = CommandHandler('shot',sendPhoto)
    #checkVTO = CommandHandler('checkvto',checkVTOSearcher)
    dispatcher.add_handler(vto_handler)
    dispatcher.add_handler(vet_handler)
    dispatcher.add_handler(screenshot)
    #dispatcher.add_handler(checkVTO)
    atoz = amazon(username,password,updater)
    atoz.updater.bot.send_message(chat_id=atoz.getChatID(), text="Vto searcher is now active...")
    atoz.updater.bot.send_message(chat_id=atoz.getChatID(), text="/vto to see all VTOS")
    atoz.updater.bot.send_message(chat_id=atoz.getChatID(), text="/vet to see all VETS")
    #atoz.updater.bot.send_message(chat_id=atoz.getChatID(), text="/checkvto to see if SearchVTO() is working")
    searchVto()
    
    


if __name__ == "__main__":
    main()
