# -*- coding: utf-8 -*-
# The skills broker

import appdaemon.plugins.hass.hassapi as hass
from collections import defaultdict


class Broker(hass.Hass):
    ''' The skills broker class'''

    def intialize(self):
        ''' Broker initialisation'''

        self.domain_triggers = defaultdict(list)
        self.service_triggers = defaultdict(list)

        for service in self.list_services():
            self.log(str(service))

    def register_domain_triggers(self, domain, triggers):
        ''' Register a domain trigger '''
        self.domain_triggers[domain].append(triggers)

    def register_service_triggers(self, service, triggers):
        ''' Register a service trigger '''
        self.service_triggers[service].append(triggers)

    def call_service(self, service, kwargs) -> str:
        ''' Call a registered service '''
        response = self.call_service(service, kwargs)
        return response