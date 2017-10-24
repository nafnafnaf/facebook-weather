# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request
#=========================================================

import unicodedata
from urllib2 import urlopen as uReq
from bs4 import BeautifulSoup as soup
reload(sys)  
sys.setdefaultencoding('utf8')


def scrape():
    url = 'http://www.meteokav.gr/weather/'
    client = uReq(url)
    page = client.read()
    client.close()
    page_soup = soup(page, "html.parser")
    values_list = [
    ["Θερμοκρασία:", page_soup.find("span", {"id":"ajaxtemp"}).text.strip()[0:6]],
    [page_soup.find_all("strong")[19].text.strip(), page_soup.find("span", {"id":"ajaxhumidity"}).text.strip()+"%"],
    ["Αίσθηση σαν: " , page_soup.find("span", {"id":"ajaxfeelslike"}).text.strip()],
    ["Διαφορά 24ώρου: ", page_soup.find_all("strong")[0].text.strip()],
    ["Διαφορά ώρας: ", page_soup.find_all("strong")[1].text.strip()],
    ["Ανεμος: " + page_soup.find("span", {"id":"ajaxwinddir"}).text.strip() + "@" + page_soup.find("span", {"id":"ajaxbeaufortnum"}).text.strip()+" Bft"], 
    [page_soup.find_all("strong")[21].text.strip() +" "+ page_soup.find("span", {"id":"ajaxbaro"}).text.strip() +" "+ page_soup.find("span", {"id":"ajaxbarotrendtext"}).text.strip()],
    ["Βροχή Σήμερα: " +  page_soup.find("span", {"id":"ajaxrain"}).text.strip()],
     #[page_soup.find("td", {"colspan":"2"}).find_all("tr")[1].find_all("td")[0].text.strip() +
    ["Μέγιστη Σήμερα: "+ page_soup.find("table", {"class":"data1"}).find_all("tr")[1].find_all("td")[1].text.strip()[0:6] +"@"+ page_soup.find("table", {"class":"data1"}).find_all("tr")[1].find_all("td")[1].text.strip()[-6:]],
    #    [page_soup.find("td", {"colspan":"2"}).find_all("tr")[1].find_all("td")[0].text.strip() +
    ["Μέγιστη Χθες: "+ page_soup.find("table", {"class":"data1"}).find_all("tr")[1].find_all("td")[2].text.strip()[0:6] +"@"+ page_soup.find("table", {"class":"data1"}).find_all("tr")[1].find_all("td")[2].text.strip()[-6:]],
    ["Ελάχιστη Σήμερα: " + page_soup.find("table", {"class":"data1"}).find_all("tr")[2].find_all("td")[1].text.strip()[0:4]+"@"+ page_soup.find("table", {"class":"data1"}).find_all("tr")[2].find_all("td")[1].text.strip()[-5:]],
    ["Ελάχιστη Χθες: " + page_soup.find("table", {"class":"data1"}).find_all("td")[5].text.strip()[0:4] +"@"+ page_soup.find("table", {"class":"data1"}).find_all("td")[5].text.strip()[-5:]],
    [ page_soup.find_all("strong")[20].text.strip() +" "+ page_soup.find("span", {"id":"ajaxdew"}).text.strip()],
    ["MAX_"+ page_soup.find_all("strong")[19].text.strip() +" "+ page_soup.find("td", {"rowspan":"3"}).find_all("tr")[1].find_all("td")[1].text.strip()[0:3] +"@"+ page_soup.find("td", {"rowspan":"3"}).find_all("tr")[1].find_all("td")[1].text.strip()[-5:]], 
    ["MAX_Baro: " + page_soup.find("td", {"rowspan":"3"}).find_all("tr")[6].find_all("td")[1].text.strip()[0:10] +"@"  + page_soup.find("td", {"rowspan":"3"}).find_all("tr")[6].find_all("td")[1].text.strip()[-5:]],
    ["MIN_Baro: " + page_soup.find("td", {"rowspan":"3"}).find_all("tr")[7].find_all("td")[1].text.strip()[0:10]+"@"+ page_soup.find("td", {"rowspan":"3"}).find_all("tr")[7].find_all("td")[1].text.strip()[-5:]]
     ]
    # y = values_list
    #uni_values = unicodedata.normalize('NFKD', y).encode('ascii', 'ignore')
    return tabulate(values_list)
sc = scrape()
#=========================================================
app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
    x = [1, 4, 0]
    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    send_message(sender_id, sc)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print u"{}: {}".format(datetime.now(), msg)
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
