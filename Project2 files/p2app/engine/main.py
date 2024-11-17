# p2app/engine/main.py
#
# ICS 33 Spring 2023
# Project 2: Learning to Fly
#
# An object that represents the engine of the application.
#
# This is the outermost layer of the part of the program that you'll need to build,
# which means that YOU WILL DEFINITELY NEED TO MAKE CHANGES TO THIS FILE.

from p2app.events import *
from p2app.engine.app_engine import process_app_event
from p2app.engine.continent_engine import process_continent_event
from p2app.engine.country_engine import process_country_event
from p2app.engine.region_engine import process_region_event

class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """
        Initialize Engine class.
        Attributes:
            connection: stores connection to input database. Before connection is created,
                it is None.
        """
        self.connection = None


    def process_event(self, event):
        """A generator function that processes one event sent from the user interface,
        yielding zero or more events in response."""

        if type(event).__name__ in ('QuitInitiatedEvent', 'OpenDatabaseEvent', 'CloseDatabaseEvent'):
            yield process_app_event(self, event)
        elif type(event).__name__ in ('StartContinentSearchEvent', 'LoadContinentEvent', 'SaveNewContinentEvent', 'SaveContinentEvent'):
            yield process_continent_event(self, event)
        elif type(event).__name__ in ('StartCountrySearchEvent', 'LoadCountryEvent', 'SaveNewCountryEvent', 'SaveCountryEvent'):
            yield process_country_event(self, event)
        elif type(event).__name__ in ('StartRegionSearchEvent', 'LoadRegionEvent', 'SaveNewRegionEvent', 'SaveRegionEvent'):
            yield process_region_event(self, event)
        else:
            yield ErrorEvent(f'Not valid event. Event given: {type(event).__name__}')

