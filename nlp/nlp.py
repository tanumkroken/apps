# -*- coding: utf-8 -*-
# The skills interface
import appdaemon.plugins.hass.hassapi as hass
import calendar

import spacy
from spacy.lang.nb.examples import sentences
# import graphviz, deplacy



class LanguageProcessor(hass.Hass):


    def initialize(self):
        # Implement the callback interface that AD expects
        # event = self.args['entity'] # The event to listen to
        # For state callbacks, a class defined callback function should look like this:
        # def my_callback(self, entity, attribute, old, new, kwargs)
        # self.base_callback(event, None, None, None,None)
        # self.listen_state(self.base_callback,event)

        # Load the nlp module
        self.nlp_no = spacy.load("nb_core_news_sm")
        self.nlp_en = spacy.load("en_core_web_sm")


    def tokenize(self, msg: str, lang: str= 'en'):
        if lang == 'no':
            doc = self.nlp_no(msg)
        else:
            doc = self.nlp_en(msg)
        if self.args['logging'] is True:
            self.log(doc.text)
        return doc.text