import sqlite3
from p2app.events import *



def process_continent_event(engine, event):
    """
    Processes four continent related events.
    Events processed, and their corresponding returned events:
        StartContinentSearchEvent
            ContinentSearchResultEvent
            None, if no continent meets search criteria
        LoadContinentEvent
            ContinentLoadedEvent
        SaveNewContinentEvent
            ContinentSavedEvent
            SaveContinentFailedEvent
        SaveContinentEvent
            ContinentSavedEvent
            SaveContinentFailedEvent
    """
    if type(event).__name__ == 'StartContinentSearchEvent':
        if start_search_continent(engine, event.continent_code(), event.name()) is not None:
            return ContinentSearchResultEvent(start_search_continent(engine, event.continent_code(), event.name()))
    elif type(event).__name__ == 'LoadContinentEvent':
        return ContinentLoadedEvent(load_continent(engine, event.continent_id()))
    elif type(event).__name__ == 'SaveNewContinentEvent':
        return try_creation(engine, event.continent())
    elif type(event).__name__ == 'SaveContinentEvent':
        return try_edit(engine, event.continent())


def start_search_continent(engine, code=None, name=None):
    """
    Search all continents that meet the criteria of user input.
    Parameters:
        engine: Engine class object created in main module.
        code: user input continent code. Default is None
        name: user input continent name. Default is None
    Returns:
        All continents that meet the criteria as Continent namedTuple objects, one at a time.
    """
    if code is None:
        cursor = engine.connection.execute(
            """
            SELECT continent_id, continent_code, name
            FROM continent
            WHERE name = ?;
            """, (name,)
        )
    elif name is None:
        cursor = engine.connection.execute(
            """
            SELECT continent_id, continent_code, name
            FROM continent
            WHERE continent_code = ?;
            """, (code,)
        )
    else:
        cursor = engine.connection.execute(
            """
            SELECT continent_id, continent_code, name
            FROM continent
            WHERE continent_code = ? AND name = ?;
            """, (code, name)
        )
    for cont in make_continent_Object(cursor):
        return cont


def load_continent(engine, continent_id):
    """
    Return continent of the selected continent id.
    Parameters:
        engine: Engine class object created in main module.
        continent_id: user input continent id.
    Returns:
        Continent namedTuple object of the chosen continent id.
    """
    cursor = engine.connection.execute(
        """
        SELECT continent_id, continent_code, name
        FROM continent
        WHERE continent_id = ?;
        """, (continent_id,)
    )
    for cont in make_continent_Object(cursor):
        return cont

def try_creation(engine, continent: Continent):
    """
    Try to create continent based on user input, handling any exceptions.
    Exceptions handled:
        sqlite3.IntegrityError
        For all other exceptions, simply return the exception's name as explanation.
    Returns:
        ContinentSavedEvent
        SaveContinentFailedEvent
    """
    try:
        return ContinentSavedEvent(create_continent(engine, continent))
    except sqlite3.IntegrityError:
        return SaveContinentFailedEvent("Continent's code must be unique values.")
    except Exception as e:
        return SaveContinentFailedEvent(f'Failed creating continent due to following error: {type(e).__name__}')

def create_continent(engine, continent: Continent):
    """
    Given continent information, create a continent inside continent table of given database.
    Also initialize missing information:
        Continent id is set to 1 plus the largest id value currently present.
        For continent code and name, if no value is given, it is set to empty string.
    Returns:
        continent namedTuple object containing created continent's information.
    """
    cont_id = generate_id(engine)

    cont_code, cont_name = initialize_var(continent)

    engine.connection.execute(
        """
        INSERT INTO continent(continent_id, continent_code, name) 
        VALUES (?, ?, ?);
        """, (int(cont_id), cont_code, cont_name)
    )

    cursor = engine.connection.execute(
        """
        SELECT continent_id, continent_code, name
        FROM continent
        WHERE continent_id = ?;
        """, (int(cont_id),)
    )
    for cont in make_continent_Object(cursor):
        return cont

def generate_id(engine):
    """
    Generates unique id for continent being created.
    Get the largest id value in the continent table of given database and add 1.
    Returns:
        Unique id as integer
    """
    cursor = engine.connection.execute(
        """
        SELECT continent_id
        FROM continent;
        """
    )
    return int(max(cursor)[0]) + 1

def try_edit(engine, continent: Continent):
    """
    Try to edit continent based on user input, handling any exceptions.
    Exceptions handled:
        sqlite3.IntegrityError
        ValueError
        For all other exceptions, simply return the exception's name as explanation.
    Returns:
        ContinentSavedEvent
        SaveContinentFailedEvent
    """
    try:
        return ContinentSavedEvent(edit_continent(engine, continent))
    except sqlite3.IntegrityError:
        return SaveContinentFailedEvent('Continent code must be unique.')
    except ValueError:
        return SaveContinentFailedEvent('Inappropriate input value.')
    except Exception as e:
        return SaveContinentFailedEvent(f'Following error occurred: {type(e).__name__}')

def edit_continent(engine, continent):
    """
    Edit information for continent already present in continent table of given database.
    Returns:
        continent namedTuple object containing edited continent's information.
    """
    cont_code, cont_name = initialize_var(continent)

    engine.connection.execute(
        """
        UPDATE continent
        SET continent_code = ?,
            name = ?
        WHERE continent_id = ?;
        """, (cont_code, cont_name, int(continent.continent_id))
    )

    cursor = engine.connection.execute(
        """
        SELECT continent_id, continent_code, name
        FROM continent
        WHERE continent_id = ?;
        """, (int(continent.continent_id),)
    )

    for cont in make_continent_Object(cursor):
        return cont

def initialize_var(continent):
    """
    Initializes attributes of continent namedTuple object to follow NOT NULL constraints.
    Returns:
        (continent code, continent name)
    """
    if continent.continent_code is None:
        cont_code = ''
    else:
        cont_code = continent.continent_code

    if continent.name is None:
        cont_name = ''
    else:
        cont_name = continent.name

    return cont_code, cont_name

def make_continent_Object(cursor):
    """
    For every row of continents in the given cursor, create and return namedTuple object of them, one at a time.
    """
    val = cursor.fetchone()
    while val:
        yield Continent(val[0], val[1], val[2])
        val = cursor.fetchone()