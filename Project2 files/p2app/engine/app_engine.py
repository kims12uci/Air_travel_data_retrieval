import sqlite3
from p2app.events import *

def process_app_event(engine, event):
    """
    Process application level events from UI and return appropriate event.
    Events processed, and their corresponding returned events:
        QuitInitiatedEvent
            EndApplicationEvent
        OpenDatabaseEvent
            DatabaseOpenedEvent
            DatabaseOpenFailedEvent
        CloseDatabaseEvent
            DatabaseClosedEvent
    """
    if type(event).__name__ == 'QuitInitiatedEvent':
        return EndApplicationEvent()
    elif type(event).__name__ == 'OpenDatabaseEvent':
        return open_database(engine, event)
    elif type(event).__name__ == 'CloseDatabaseEvent':
        engine.connection = None
        return DatabaseClosedEvent()

def open_database(engine, event):
    """
    Try to open given database, handling any exceptions.
    Exceptions handled:
        FileNotFoundError
        IsADirectoryError
        For all other exceptions, simply return the exception's name as explanation.
    Returns:
        DatabaseOpenedEvent
    """
    try:
        return connect_database(engine, event)
    except FileNotFoundError:
        return DatabaseOpenFailedEvent('Database file is not found.')
    except IsADirectoryError:
        return DatabaseOpenFailedEvent('Given path is a directory.')
    except Exception as E:
        return DatabaseOpenFailedEvent(f'Following exception occurred: {type(E).__name__}')


def connect_database(engine, event):
    """
    Given a path to a Database, create a connection object and save it to connection attribute of Engine class.
    Also enforces data integrity.
    Exceptions raised:
        FileNotFoundError
        IsADirectoryError
    Returns:
        DatabaseOpenedEvent
    """
    p = Path(event.path())
    if not p.exists():
        raise FileNotFoundError
    if p.is_dir():
        raise IsADirectoryError

    engine.connection = sqlite3.connect(event.path())
    engine.connection.execute('PRAGMA foreign_keys = ON;')
    return DatabaseOpenedEvent(event.path())