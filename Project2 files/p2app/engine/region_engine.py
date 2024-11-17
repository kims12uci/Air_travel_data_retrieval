from p2app.events import *
import sqlite3
def process_region_event(engine, event):
    """
    Processes four country related events.
    Events processed, and their corresponding returned events:
        StartRegionSearchEvent
            RegionSearchResultEvent
            None, if no country meets search criteria
        LoadRegionEvent
            RegionLoadedEvent
        SaveNewRegionEvent
            RegionSavedEvent
            SaveRegionFailedEvent
        SaveRegionEvent
            RegionSavedEvent
            SaveRegionFailedEvent
    """
    if type(event).__name__ == 'StartRegionSearchEvent':
        if start_search_region(engine, event.region_code(), event.local_code(), event.name()) is not None:
            return RegionSearchResultEvent(start_search_region(engine, event.region_code(), event.local_code(), event.name()))
    elif type(event).__name__ == 'LoadRegionEvent':
        return RegionLoadedEvent(load_region(engine, event.region_id()))
    elif type(event).__name__ == 'SaveNewRegionEvent':
        return try_creation(engine, event.region())
    elif type(event).__name__ == 'SaveRegionEvent':
        return try_edit(engine, event.region())

def start_search_region(engine, code=None, local_code=None, name=None):
    """
    Search all regions that meet the criteria of user input.
    Parameters:
        engine: Engine class object created in main module.
        code: user input region code. Default is None
        local_code: user input local code. Default is None
        name: user input region name. Default is None
    Returns:
        All regions that meet the criteria as Region namedTuple objects, one at a time.
    """
    if (code is None) and (local_code is None):
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM region
            WHERE name = ?;
            """, (name,)
        )
    elif (code is None) and (name is None):
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM region
            WHERE local_code = ?;
            """, (local_code,)
        )
    elif (local_code is None) and (name is None):
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM region
            WHERE region_code = ?;
            """, (code,)
        )
    elif code is None:
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM region
            WHERE local_code = ? AND name = ?;
            """, (local_code, name)
        )
    elif local_code is None:
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM region
            WHERE region_code = ? AND name = ?;
            """, (code, name)
        )
    elif name is None:
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM region
            WHERE region_code = ? AND local_code = ?;
            """, (code, local_code)
        )
    else:
        cursor = engine.connection.execute(
            """
            SELECT *
            FROM region
            WHERE region_code = ? AND local_code = ? AND name = ?;
            """, (code, local_code, name)
        )

    for region in make_region_Object(cursor):
        return region

def load_region(engine, region_id):
    """
    Return region of the selected region id.
    Parameters:
        engine: Engine class object created in main module.
        region_id: user input region id.
    Returns:
        Region namedTuple object of the chosen region id.
    """
    cursor = engine.connection.execute(
        """
        SELECT *
        FROM region
        WHERE region_id = ?;
        """, (region_id,)
    )
    for reg in make_region_Object(cursor):
        return reg

def try_creation(engine, region: Region):
    """
    Try to create region based on user input, handling any exceptions.
    Exceptions handled:
        sqlite3.IntegrityError
        For all other exceptions, simply return the exception's name as explanation.
    Returns:
        RegionSavedEvent
        SaveRegionFailedEvent
    """
    try:
        return RegionSavedEvent(create_region(engine, region))
    except sqlite3.IntegrityError:
        return SaveRegionFailedEvent("Region's code must be unique values, and continent, country id must be valid.")
    except Exception as e:
        return SaveRegionFailedEvent(f'Failed creating country due to following error: {type(e).__name__}')

def create_region(engine, region: Region):
    """
    Given region information, create it inside region table of given database.
    Also initialize missing information:
        region id is set to 1 plus the largest id value currently present.
        For region code, local code, and name, if no value is given, it is set to empty string.
        For continent and country id, if no value is given, it is set to following values:
            If both are missing, continent id is 1 and country id is the smallest value possible in the continent.
            If only continent id is missing, given country's continent id is used.
            If only country id is missing, the smallest country id in given continent is used.
        For wikipedia link and keyword, if empty string or no value is given, it is set to NULL.
    Returns:
        Region namedTuple object containing created country's information.
    """
    region_id = generate_id(engine)

    region_code, local_code, region_name, region_cont_id, region_country_id, region_wiki, region_kw = initialize_var(engine, region)

    engine.connection.execute(
        """
        INSERT INTO region(region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, keywords) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (int(region_id), region_code, local_code, region_name, int(region_cont_id), int(region_country_id), region_wiki, region_kw)
    )

    cursor = engine.connection.execute(
        """
        SELECT *
        FROM region
        WHERE region_id = ?;
        """, (int(region_id),)
    )
    for reg in make_region_Object(cursor):
        return reg

def generate_id(engine):
    """
    Generates unique id for region being created.
    Get the largest id value in the region table of given database and add 1.
    Returns:
        Unique id as integer
    """
    cursor = engine.connection.execute(
        """
        SELECT region_id
        FROM region;
        """
    )
    return int(max(cursor)[0]) + 1

def try_edit(engine, region: Region):
    """
    Try to edit region based on user input, handling any exceptions.
    Exceptions handled:
        sqlite3.IntegrityError
        ValueError
        For all other exceptions, simply return the exception's name as explanation.
    Returns:
        RegionSavedEvent
        SaveRegionFailedEvent
    """
    try:
        return RegionSavedEvent(edit_region(engine, region))
    except sqlite3.IntegrityError:
        return SaveRegionFailedEvent('region code must be unique. Continent, country id must be valid and matching.')
    except ValueError:
        return SaveRegionFailedEvent('Inappropriate input value.')
    except Exception as e:
        return SaveRegionFailedEvent(f'Following error occurred: {type(e).__name__}')

def edit_region(engine, region):
    """
    Edit information for region already present in region table of given database.
    Returns:
        Region namedTuple object containing edited region's information.
    """
    region_code, local_code, region_name, region_cont_id, region_country_id, region_wiki, region_kw = initialize_var(engine, region)

    check_cont_country_match(engine, region_cont_id, region_country_id)

    engine.connection.execute(
        """
        UPDATE region
        SET region_code = ?,
            local_code = ?,
            name = ?,
            continent_id = ?,
            country_id = ?,
            wikipedia_link = ?,
            keywords = ?
        WHERE region_id = ?;
        """, (region_code, local_code, region_name, int(region_cont_id), int(region_country_id), region_wiki, region_kw, region.region_id)
    )

    cursor = engine.connection.execute(
        """
        SELECT *
        FROM region
        WHERE region_id = ?;
        """, (int(region.region_id),)
    )

    for reg in make_region_Object(cursor):
        return reg

def check_cont_country_match(engine, region_cont_id, region_country_id):
    if not get_cont(engine, region_country_id) == region_cont_id:
        raise sqlite3.IntegrityError


def initialize_var(engine, region):
    """
    Initialize missing information to follow database integrity.
        For region code, local code, and name, if no value is given, it is set to empty string.
        For continent and country id, if no value is given, it is set to following values:
            If both are missing, continent id is 1 and country id is the smallest value possible in the continent.
            If only continent id is missing, given country's continent id is used.
            If only country id is missing, the smallest country id in given continent is used.
        For wikipedia link and keyword, if empty string or no value is given, it is set to NULL.
    """
    if region.region_code is None:
        region_code = ''
    else:
        region_code = region.region_code

    if region.local_code is None:
        local_code = ''
    else:
        local_code = region.local_code

    if region.name is None:
        region_name = ''
    else:
        region_name = region.name

    if ((region.continent_id == False) or (region.continent_id is None)) and ((region.country_id == False) or (region.country_id is None)):
        region_cont_id = 1
        region_country_id = find_country_id(engine, 1)
    elif (region.continent_id == False) or (region.continent_id is None):
        region_country_id = region.country_id
        region_cont_id = get_cont(engine, region_country_id)
    elif (region.country_id == False) or (region.country_id is None):
        region_cont_id = region.continent_id
        region_country_id = find_country_id(engine, region_cont_id)
    else:
        region_cont_id = region.continent_id
        region_country_id = region.country_id

    if not region.wikipedia_link:
        region_wiki = None
    else:
        region_wiki = region.wikipedia_link

    if not region.keywords:
        region_kw = None
    else:
        region_kw = region.keywords

    return region_code, local_code, region_name, region_cont_id, region_country_id, region_wiki, region_kw

def find_country_id(engine, cont_id):
    """
    Given a continent id, find the smallest country and return its id.
    """
    cursor = engine.connection.execute(
        """
        SELECT country_id
        FROM country
        WHERE continent_id = ?;
        """, (int(cont_id),)
    )
    return int(min(cursor)[0])

def get_cont(engine, country_id):
    """
    Given a country id, find the continent it belongs to and return the continent's id.
    """
    cursor = engine.connection.execute(
        """
        SELECT continent_id
        FROM country
        WHERE country_id = ?;
        """, (int(country_id),)
    )
    return int(max(cursor)[0])

def make_region_Object(cursor):
    """
    For every row of regions in the given cursor, create and return Region namedTuple object of them, one at a time.
    """
    val = cursor.fetchone()
    while val:
        if val[6] is None:
            wiki = ''
        else:
            wiki = val[6]

        if val[7] is None:
            kw = ''
        else:
            kw = val[7]
        yield Region(val[0], val[1], val[2], val[3], val[4], val[5], wiki, kw)
        val = cursor.fetchone()