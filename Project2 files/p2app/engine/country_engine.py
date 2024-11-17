from p2app.events import *
import sqlite3

def process_country_event(engine, event):
    """
    Processes four country related events.
    Events processed, and their corresponding returned events:
        StartCountrySearchEvent
            CountrySearchResultEvent
            None, if no country meets search criteria
        LoadCountryEvent
            CountryLoadedEvent
        SaveNewCountryEvent
            CountrySavedEvent
            SaveCountryFailedEvent
        SaveCountryEvent
            CountrySavedEvent
            SaveCountryFailedEvent
    """
    if type(event).__name__ == 'StartCountrySearchEvent':
        if start_search_country(engine, event.country_code(), event.name()) is not None:
            return CountrySearchResultEvent(start_search_country(engine, event.country_code(), event.name()))
    elif type(event).__name__ == 'LoadCountryEvent':
        return CountryLoadedEvent(load_country(engine, event.country_id()))
    elif type(event).__name__ == 'SaveNewCountryEvent':
        return try_creation(engine, event.country())
    elif type(event).__name__ == 'SaveCountryEvent':
        return try_edit(engine, event.country())

def start_search_country(engine, code=None, name=None):
    """
    Search all countries that meet the criteria of user input.
    Parameters:
        engine: Engine class object created in main module.
        code: user input country code. Default is None
        name: user input country name. Default is None
    Returns:
        All countries that meet the criteria as Country namedTuple objects, one at a time.
    """
    if code is None:
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM country
            WHERE name = ?;
            """, (name,)
        )
    elif name is None:
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM country
            WHERE country_code = ?;
            """, (code,)
        )
    else:
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM country
            WHERE country_code = ? AND name = ?;
            """, (code, name)
        )
    for country in make_country_Object(cursor):
        return country

def load_country(engine, country_id):
    """
    Return country of the selected country id.
    Parameters:
        engine: Engine class object created in main module.
        country_id: user input country id.
    Returns:
        country namedTuple object of the chosen country id.
    """
    cursor = engine.connection.execute(
        """
        SELECT *
        FROM country
        WHERE country_id = ?;
        """, (country_id,)
    )
    for country in make_country_Object(cursor):
        return country

def try_creation(engine, country: Country):
    """
    Try to create country based on user input, handling any exceptions.
    Exceptions handled:
        sqlite3.IntegrityError
        For all other exceptions, simply return the exception's name as explanation.
    Returns:
        CountrySavedEvent
        SaveCountryFailedEvent
    """
    try:
        return CountrySavedEvent(create_country(engine, country))
    except sqlite3.IntegrityError:
        return SaveCountryFailedEvent("Country's code must be unique values, and continent id must be valid.")
    except Exception as e:
        return SaveCountryFailedEvent(f'Failed creating country due to following error: {type(e).__name__}')

def create_country(engine, country: Country):
    """
    Given country information, create it inside country table of given database.
    Also initialize missing information:
        country id is set to 1 plus the largest id value currently present.
        For country code, name, and wikipedia link, if no value is given, it is set to empty string.
        For continent id, if no value is given, it is set to 1.
        For keyword, if empty string or no value is given, it is set to NULL.
    Returns:
        Country namedTuple object containing created country's information.
    """
    country_id = generate_id(engine)

    country_code, country_name, country_wiki, country_cont_id, country_kw = initialize_var(country)

    engine.connection.execute(
        """
        INSERT INTO country(country_id, country_code, name, continent_id, wikipedia_link, keywords) 
        VALUES (?, ?, ?, ?, ?, ?);
        """, (int(country_id), country_code, country_name, int(country_cont_id), country_wiki, country_kw)
    )

    cursor = engine.connection.execute(
        """
        SELECT *
        FROM country
        WHERE country_id = ?;
        """, (int(country_id),)
    )
    for country in make_country_Object(cursor):
        return country

def generate_id(engine):
    """
    Generates unique id for country being created.
    Get the largest id value in the country table of given database and add 1.
    Returns:
        Unique id as integer
    """
    cursor = engine.connection.execute(
        """
        SELECT country_id
        FROM country;
        """
    )
    return int(max(cursor)[0]) + 1

def try_edit(engine, country: Country):
    """
    Try to edit country based on user input, handling any exceptions.
    Exceptions handled:
        sqlite3.IntegrityError
        ValueError
        For all other exceptions, simply return the exception's name as explanation.
    Returns:
        CountrySavedEvent
        SaveCountryFailedEvent
    """
    try:
        return CountrySavedEvent(edit_country(engine, country))
    except sqlite3.IntegrityError:
        return SaveCountryFailedEvent('country code must be unique and continent id must be valid.')
    except ValueError:
        return SaveCountryFailedEvent('Inappropriate input value.')
    except Exception as e:
        return SaveCountryFailedEvent(f'Following error occurred: {type(e).__name__}')


def edit_country(engine, country):
    """
    Edit information for country already present in country table of given database.
    Returns:
        Country namedTuple object containing edited country's information.
    """
    country_code, country_name, country_wiki, country_cont_id, country_kw = initialize_var(country)

    engine.connection.execute(
        """
        UPDATE country
        SET country_code = ?,
            name = ?,
            continent_id = ?,
            wikipedia_link = ?,
            keywords = ?
        WHERE country_id = ?;
        """, (country_code, country_name, int(country_cont_id), country_wiki, country_kw, country.country_id)
    )

    cursor = engine.connection.execute(
        """
        SELECT *
        FROM country
        WHERE country_id = ?;
        """, (int(country.country_id),)
    )

    for country in make_country_Object(cursor):
        return country

def initialize_var(country):
    """
    Initializes attribute values of given Country object to follow NOT NULL.
        For country code, name, and wikipedia link, if no value is given, it is set to empty string.
        For continent id, if no value or 0 is given, it is set to 1.
        For keyword, if empty string or no value is given, it is set to NULL.
    """
    if country.country_code is None:
        country_code = ''
    else:
        country_code = country.country_code

    if country.name is None:
        country_name = ''
    else:
        country_name = country.name

    if country.wikipedia_link is None:
        country_wiki = ''
    else:
        country_wiki = country.wikipedia_link

    if (country.continent_id == False) or (country.continent_id is None):
        country_cont_id = 1
    else:
        country_cont_id = country.continent_id

    if not country.keywords:
        country_kw = None
    else:
        country_kw = country.keywords

    return country_code, country_name, country_wiki, country_cont_id, country_kw

def make_country_Object(cursor):
    """
    For every row of countries in the given cursor, create and return Country namedTuple object of them, one at a time.
    """
    val = cursor.fetchone()
    while val:
        if val[5] is None:
            kw = ''
        else:
            kw = val[5]
        yield Country(val[0], val[1], val[2], val[3], val[4], kw)
        val = cursor.fetchone()