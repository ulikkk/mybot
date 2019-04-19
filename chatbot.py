import nltk
import numpy as np
import random
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests  
import datetime
from flask import Flask, request
from pymessenger.bot import Bot

token = '861166623:AAFvtGw-K1na46gOMBmIAKcG-v-0GDCtJaI' #Telegram
app = Flask(__name__)
# Facebook tokens
ACCESS_TOKEN = 'EAAWYaBcmpSEBAJsDg3D9dKcs7a6CwZB3bvhFqQA4cL8ZB5aV9XD1beXTRYKUCaOcy074brVEEAyaO7NdmjHtDGCO5dH4Mh3uJEmmfG6Aad9Dsab1HoA25tcfGsFDgnNFWO9esvnnsP0ZCqPUPrVyiZAzyQ7QApZCE6ZBQT6XjORwZDZD'
VERIFY_TOKEN = 'TESTINGTOKEN'
bot = Bot(ACCESS_TOKEN)

class BotHandler:    

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = get_result[len(get_result)]

        return last_update


bot_url = BotHandler(token)  
now = datetime.datetime.now()  

f=open('chatbot.txt','r',errors = 'ignore')

raw=f.read()

raw=raw.lower()# converts to lowercase

sent_tokens = nltk.sent_tokenize(raw)# converts to list of sentences
word_tokens = nltk.word_tokenize(raw)# converts to list of words


lemmer = nltk.stem.WordNetLemmatizer()
#WordNet is a semantically-oriented dictionary of English included in NLTK.
def LemTokens(tokens):
    return [lemmer.lemmatize(token) for token in tokens]
remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
def LemNormalize(text):
    return LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))

GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up","hey",)

GREETING_RESPONSES = ["hi", "hey", "*nods*", "hi there", "hello", "I am glad! You are talking to me"]

def greeting(sentence):
    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)

def response(user_response):
    robo_response=''
    sent_tokens.append(user_response)
    TfidfVec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')
    tfidf = TfidfVec.fit_transform(sent_tokens)
    vals = cosine_similarity(tfidf[-1], tfidf)
    idx=vals.argsort()[0][-2]
    flat = vals.flatten()
    flat.sort()
    req_tfidf = flat[-2]
    if(req_tfidf==0):
        robo_response=robo_response+"I am sorry! I don't understand you"
        return robo_response
    else:
        robo_response = robo_response+sent_tokens[idx]
        return robo_response

def main():  
    flag=True
    new_offset = None
    last_update = bot_url.get_last_update()
    last_chat_id = last_update['message']['chat']['id']
    last_chat_name = last_update['message']['chat']['first_name']
    bot_url.send_message(last_chat_id, 'My name is Robo. I will answer your queries about Chatbots. If you want to exit, type Bye, {}'.format(last_chat_name))
    while(flag==True):
        bot_url.get_updates(new_offset)
        last_update = bot_url.get_last_update()
        last_update_id = last_update['update_id']
        last_chat_text = last_update['message']['text']
        last_chat_id = last_update['message']['chat']['id']
        last_chat_name = last_update['message']['chat']['first_name']
        user_response = last_chat_text
        user_response = user_response.lower()
        if(user_response!='bye'):
            if(user_response=='thanks' or user_response=='thank you' ):
                new_offset = last_update_id + 1
                flag=False
                bot_url.send_message(last_chat_id, 'You are welcome, {}'.format(last_chat_name))
            else:
                if(greeting(user_response)!=None):               
                    bot_url.send_message(last_chat_id, (greeting(user_response))+ ', {}'.format(last_chat_name))
                    new_offset = last_update_id + 1
                else:
                    bot_url.send_message(last_chat_id, (response(user_response)))
                    sent_tokens.remove(user_response)
                    new_offset = last_update_id + 1
        else:
            flag=False
            bot_url.send_message(last_chat_id, 'Bye! take care, {}'.format(last_chat_name))

@app.route("/", methods=['GET', 'POST'])
def receive_message():
    flag=True
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook.""" 
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                if (message['message'].get('text'))!='bye':
                    if(message['message'].get('text') =='thanks' or message['message'].get('text') =='thank you' ):
                        #Facebook Messenger ID for user so we know where to send response back to
                        recipient_id = message['sender']['id']
                        response_sent_text = 'You are welcome'
                        send_message(recipient_id, response_sent_text)
                    else:
                        if(greeting(message['message']['text'])!=None):
                            recipient_id = message['sender']['id']
                            response_sent_text = greeting(message['message']['text'])
                            send_message(recipient_id, response_sent_text)
                        else:
                            recipient_id = message['sender']['id']
                            response_sent_text = response(message['message']['text'])
                            send_message(recipient_id, response_sent_text)
                            sent_tokens.remove(message['message']['text'])
                else:
                    recipient_id = message['sender']['id']
                    response_sent_text = 'Bye! take care'
                    send_message(recipient_id, response_sent_text)
    return "Message Processed"
 
def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def send_message(recipient_id, response):
    '''Отправляет пользователю текстовое сообщение в соответствии с параметром response.'''
    bot.send_text_message(recipient_id, response)
    return 'Success'

def get_message():
    '''Отправляет случайные сообщения пользователю.'''
    sample_responses = ["Потрясающе!", "Я вами горжусь!", "Продолжайте в том же духе!", "Лучшее, что я когда-либо видел!"]
    return random.choice(sample_responses)
   
        
if __name__ == '__main__':  
    try:
        main()
        app.run()
    except KeyboardInterrupt:
        exit()
