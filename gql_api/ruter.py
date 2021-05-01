import hassapi as hass
from collections import defaultdict
from datetime import datetime
from python_graphql_client import GraphqlClient

"""
Get travel info for Viken public transport
Arguments:
 - local_stop_id: Your preferred local public transportation stop code registered by entur.io (NSR:StopPlace:4122)
 - departures: Number of departures to query
 - time_range: The time range to query in minutes
 - interval: The update interval time in minutes
 - ET-Client-Name: The client name to be provided by the REST header, required by entur.io
"""

ENTUR_API='https://api.entur.io/journey-planner/v2/graphql'  # One common stop for all public transport in Norway & Sweden
GEOCODER_AUTOCOMPLETE='https://api.entur.io/geocoder/v1/autocomplete?' # The url for geo look-ups
PARAMS = '&boundary.country=NOR&boundary.county_ids=KVE:TopographicPlace:30&lang=no&text={}' # Restrict search to Norway, Viken=30

# Departure board query - full form
GRAPHQL_DEPARTURES_FULL = '''
{
  stopPlace(id: $stop_id) {
    id
    name
    estimatedCalls(timeRange: $time_range, numberOfDepartures: $n_departures) {
      realtime
      aimedArrivalTime
      aimedDepartureTime
      expectedArrivalTime
      expectedDepartureTime
      actualArrivalTime
      actualDepartureTime
      date
      forBoarding
      forAlighting
      destinationDisplay {
        frontText
      }
      quay {
        id
      }
      serviceJourney {
        journeyPattern {
          line {
            id
            name
            transportMode
          }
        }
      }
    }
  }
}'''

# Next departure query
GRAPHQL_NEXT_DEPARTURE = '''
{
  stopPlace(id:\"$stop_place\") {
    name
    id
    estimatedCalls {
      expectedDepartureTime
      destinationDisplay {
        frontText
      }
      serviceJourney {
        line {
          publicCode
          transportMode
        }
      }
    }
  }
}
'''

class Ruter(hass.Hass):

    def initialize(self):
        # Create the GQL client
        ENDPOINT = self.args['gql_server'] # One common stop for all public transport in Norway & Sweden
        self.client = GraphqlClient(endpoint=ENDPOINT)
        if self.args['logging'] is True:
            self.log('Initialized GQL client for {}'.format(ENDPOINT), ascii_encode=False)

        self.header = {
            "ET-Client-Name": self.args['ET-Client-Name'],
            "cache-control": "no-cache, no-store, max-age=0, must-revalidate",
            "content-type": "application/json;charset=utf-8",
            "expires": "0",
            "pragma": "no-cache"
        }
        now = self.get_now()
        interval = int(self.args["interval"])
        #self.run_every(self.updateState, now, interval * 60)

    def query(self, query, header) -> dict:
        payload = self.client.execute(query=query, headers=header)
        return payload

    def updateState(self, kwargs=None):
        departures = self.queryNextDeparturesFromYourLocalStop()
        self.set_app_state(self.args['entity'], {"state": "", "attributes": departures})

    def queryNextDeparturesFromYourLocalStop(self):
        stop_id = self.args['local_stop_id']
        # Execute the query
        header = self.header
        query = GRAPHQL_NEXT_DEPARTURE.replace('$stop_place',stop_id)
        data = self.client.query(query=query, headers=header)
        d = data['data']
        stop_name = d['stopPlace']['name']
        table = defaultdict(list)
        for call in d['stopPlace']['estimatedCalls']:
            table[call['expectedDepartureTime']].append({'destination':call['destinationDisplay']['frontText']})
            table[call['expectedDepartureTime']].append({'transportMode':call['serviceJourney']['line']['transportMode']})
            table[call['expectedDepartureTime']].append({'publicCode':call['serviceJourney']['line']['publicCode']})
        if self.args['logging'] is True:
            for key in table:
                self.log(key + ': ' + str(table[key]), ascii_encode=False)
        return table