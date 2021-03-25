# -*- coding: utf-8 -*-
# The skills broker

import appdaemon.plugins.hass.hassapi as hass

class Broker(hass.Hass):
    ''' The skills broker class'''

    def intialize(self):
        ''' Broker initialisation'''

    def do_skill(self, skill):
        ''' A dispatcher for  the app skill'''
        for app in self.registered_skill:
            method = getattr(app, 'dispatch') # getattr() Will return the handle to the named method of the app
            return method(skill_to_do) # Will call the dispatch method in the app which executes the skill