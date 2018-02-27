#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tweepy.streaming import StreamListener
#coorelation
#event trigger

import re
import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)
from tweepy import OAuthHandler
from tweepy import Stream
import tweepy
from dateutil import parser
from nltk_contrib.timex import *
from BeautifulSoup import BeautifulSoup
import datetime
from nltk.corpus import wordnet
from nltk.tag import StanfordNERTagger

# Variables that contains yours credentials to access Twitter API
access_token = "2920199964-ZXhU2x0QMOiAC3tZbrAZ2pRp2MDAwuNAyP8QR4a"
access_token_secret = "xiKYh1rM8D1tjWXG4SoVRJhr3pNCYkYmKgUXh7Hh3yKcH"
consumer_key = "p3OkG8bp2g5ks1qwylmaAArrb"
consumer_secret = "GRmsW4RLZbqtsKFK66NeGB6NhFsGTgtgqMCsVPHYOWuXZXKWXS"
stanford_NER_jar_folder = "/Users/devendralad/Downloads/Python_NeededPackages_NLP_Project/"
stanford_NER_jar_path = "/Users/devendralad/Downloads/Python_NeededPackages_NLP_Project/stanford-ner.jar"

#other golbal variables needed
EVENT_TYPES = ['birthday', 'meeting', 'conference', 'summit', 'launch', 'release', 'performance', 'anniversary', 'concert']
SYNONYM_SET = {}
#Set True TO print all Logs and not just the Output
All_logs = True

class TwitterStreamListener(tweepy.StreamListener):
    """ A listener handles tweets are the received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def on_status(self, status):
        process_tweet(status)
    # Twitter error list : https://dev.twitter.com/overview/api/response-codes
    def on_error(self, status_code):
        if status_code == 403:
            print("The request is understood, but it has been refused or access is not allowed. Limit is maybe reached")
            return False


def process_tweet(tweet):
    #Temporal expression Resolution & checking for valid dates
    #For the scope of project we are just considering events that are strongly associated with a particular date.
    eventDate = checkForDate(tweet)
    tweetText = tweet.text
    eventType = None
    eventLocation = None
    # Filter tweets those don't contain dates or mention of a certain day
    if(eventDate != None):
        if(datetime.date.today() > eventDate):
            if(All_logs):
                print("**DISCARDED TWEET (Past Event): " + tweetText)
                print("Event Date: " + str(eventDate) + " Today's Date: " + str(datetime.date.today()))
        else:
            #Check if Event is one of EVENT_TYPES
            eventType = checkForEvent(tweetText)
            if(eventType == None):
                if(All_logs):
                    print("**DISCARDED TWEET (Event Category not supported): " + tweetText)
            else:
                eventLocation = checkForLocation(tweetText)
                if(eventLocation == "" and tweet.user.location != None):
                    eventLocation = tweet.user.location
                #print("Event Location: " + eventLocation + " Event Date: " + str(eventDate) + " Event Type: " + eventType + "\n")
                event_entity = (eventDate, eventLocation, eventType, tweetText)
                print(event_entity)

def checkForDate(tweet):
    #resolves temporal expression using Timex.py and returns absolute date if found one
    eventDate = None
    try:
        tagged = ground(tag(tweet.text), gmt())
        soupObj = BeautifulSoup(tagged)
        if (soupObj.find('timex2') != None):
            dateString = soupObj.timex2['val']
            # got the date object
            eventDate = datetime.datetime.strptime(dateString, '%Y-%m-%d').date()
    except:
        #if any exceptions for parsing date or not finding it, just keep going.
        pass
    return eventDate

def checkForEvent(tweetText):
    eventType = None
    #check for the event in Synonem Set obtained from WordNet
    for event in SYNONYM_SET:
        for synonym in SYNONYM_SET[event]:
            if synonym in tweetText.lower():
                eventType = event
    return eventType

def checkForLocation(tweetText):
    entities = []
    try:
        nerTagger = StanfordNERTagger(stanford_NER_jar_folder + '/classifiers/english.muc.7class.distsim.crf.ser.gz', stanford_NER_jar_path)
        entities = nerTagger.tag(tweetText.split())
    except:
        pass

    result = ""
    for entity in entities:
        if entity[1] != 'O':
            result += " {}".format(entity[0])
    return result

def initialize_syn_set():
    # get all synonyms for given keywords
    global SYNONYM_SET
    for event in EVENT_TYPES:
        lemmas = []
        synsets = wordnet.synsets(event)
        for syn in synsets:
            lemmas += [re.sub("_", " ", lemma.name()) for lemma in syn.lemmas()]
        SYNONYM_SET[event] = list(set(lemmas))

def initialize_twitter_stream():
    # This handles Twitter authetification and the connection to Twitter Streaming API
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    streamListener = TwitterStreamListener()
    stream = Stream(auth, streamListener)
    # This line filter tweets from the words.
    stream.filter(languages=["en"], track=['a', 'at', 'the', 'for', 'is', 'are', 'will', 'they', 'he', 'she', 'it', 'and', 'or', 'last'])

if __name__ == '__main__':
    initialize_syn_set()
    # print(SYNONYM_SET)
    initialize_twitter_stream()