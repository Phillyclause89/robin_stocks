"""Contains decorator functions and functions for interacting with global data.

Functions
---------
    - request_document
    - request_get
    - request_post
    - update_session
"""
from functools import wraps

import requests
from robin_stocks.globals import LOGGED_IN, SESSION, OUTPUT


def set_login_state(logged_in):
    """Sets the login state"""
    global LOGGED_IN
    LOGGED_IN = logged_in


def set_output(output):
    """Sets the global output stream"""
    global OUTPUT
    OUTPUT = output


def get_output():
    """Gets the current global output stream"""
    global OUTPUT
    return OUTPUT


def login_required(func):
    """A decorator for indicating which methods require the user to be logged
       in."""

    @wraps(func)
    def login_wrapper(*args, **kwargs):
        global LOGGED_IN
        if not LOGGED_IN:
            raise Exception('{} can only be called when logged in'.format(
                func.__name__))
        return (func(*args, **kwargs))

    return (login_wrapper)


def convert_none_to_string(func):
    """A decorator for converting a None Type into a blank string"""

    @wraps(func)
    def string_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result:
            return (result)
        else:
            return ("")

    return (string_wrapper)


def id_for_stock(symbol):
    """Takes a stock ticker and returns the instrument id associated with the stock.

    :param symbol: The symbol to get the id for.
    :type symbol: str
    :returns:  A string that represents the stocks instrument id.

    """
    try:
        symbol = symbol.upper().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return (None)

    url = 'https://api.robinhood.com/instruments/'
    payload = {'symbol': symbol}
    data = request_get(url, 'indexzero', payload)

    return (filter_data(data, 'id'))


def id_for_chain(symbol):
    """Takes a stock ticker and returns the chain id associated with a stocks option.

    :param symbol: The symbol to get the id for.
    :type symbol: str
    :returns:  A string that represents the stocks options chain id.

    """
    try:
        symbol = symbol.upper().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return (None)

    url = 'https://api.robinhood.com/instruments/'

    payload = {'symbol': symbol}
    data = request_get(url, 'indexzero', payload)

    if data:
        return (data['tradable_chain_id'])
    else:
        return (data)


def id_for_group(symbol):
    """Takes a stock ticker and returns the id associated with the group.

    :param symbol: The symbol to get the id for.
    :type symbol: str
    :returns:  A string that represents the stocks group id.

    """
    try:
        symbol = symbol.upper().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return (None)

    url = 'https://api.robinhood.com/options/chains/{0}/'.format(
        id_for_chain(symbol))
    data = request_get(url)
    return (data['underlying_instruments'][0]['id'])


def id_for_option(symbol, expirationDate, strike, optionType):
    """Returns the id associated with a specific option order.

    :param symbol: The symbol to get the id for.
    :type symbol: str
    :param expirationData: The expiration date as YYYY-MM-DD
    :type expirationData: str
    :param strike: The strike price.
    :type strike: str
    :param optionType: Either call or put.
    :type optionType: str
    :returns:  A string that represents the stocks option id.

    """
    symbol = symbol.upper()
    chain_id = id_for_chain(symbol)
    payload = {
        'chain_id': chain_id,
        'expiration_dates': expirationDate,
        'strike_price': strike,
        'type': optionType,
        'state': 'active'
    }
    url = 'https://api.robinhood.com/options/instruments/'
    data = request_get(url, 'pagination', payload)

    listOfOptions = [item for item in data if item["expiration_date"] == expirationDate]
    if (len(listOfOptions) == 0):
        print(
            'Getting the option ID failed. Perhaps the expiration date is wrong format, or the strike price is wrong.',
            file=get_output())
        return (None)

    return (listOfOptions[0]['id'])


def round_price(price):
    """Takes a price and rounds it to an appropriate decimal place that Robinhood will accept.

    :param price: The input price to round.
    :type price: float or int
    :returns: The rounded price as a float.

    """
    price = float(price)
    if price <= 1e-2:
        returnPrice = round(price, 6)
    elif price < 1e0:
        returnPrice = round(price, 4)
    else:
        returnPrice = round(price, 2)

    return returnPrice


def convert_dtypes(data):
    """
    Converts to float:
                "adjusted_mark_price", "ask_price", "bid_price", "break_even_price",
                "high_price", "last_trade_price", "low_price", "mark_price",
                "previous_close_price", "chance_of_profit_long", "chance_of_profit_short",
                "delta", "gamma", "implied_volatility", "rho", "theta", "vega",
                "high_fill_rate_buy_price", "high_fill_rate_sell_price", "low_fill_rate_buy_price",
                "low_fill_rate_sell_price", "last_extended_hours_trade_price", "previous_close",
                "adjusted_previous_close", "below_tick", "above_tick", "estimate", "actual", "cutoff_price",
                "open", "high", "low", "average_volume_2_weeks", "average_volume", "high_52_weeks",
                "dividend_yield", "low_52_weeks", "market_cap", "pb_ratio", "pe_ratio", "shares_outstanding",
                "margin_initial_ratio", "maintenance_ratio", "day_trade_ratio", "default_collar_fraction",
                "underlying_price", "total_cash_amount", "quantity", "actual", "estimate",
    Converts to int:
                "trade_value_multiplier", "year", "quarter", "ask_size", "bid_size",
                "last_trade_size", "open_interest", "volume",  "float", "num_employees"
                "year_founded", "num_buy_ratings", "num_sell_ratings", "num_hold_ratings",

    :param data: The data passed into filter_data.
    :returns:  The dict with numerical types for the data from certain keys
    """
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], (dict, list)):
                data[key] = convert_dtypes(data[key])
            elif key in {
                "adjusted_mark_price", "ask_price", "bid_price", "break_even_price",
                "high_price", "last_trade_price", "low_price", "mark_price",
                "previous_close_price", "chance_of_profit_long", "chance_of_profit_short",
                "delta", "gamma", "implied_volatility", "rho", "theta", "vega",
                "high_fill_rate_buy_price", "high_fill_rate_sell_price", "low_fill_rate_buy_price",
                "low_fill_rate_sell_price", "last_extended_hours_trade_price", "previous_close",
                "adjusted_previous_close", "below_tick", "above_tick", "estimate", "actual", "cutoff_price",
                "open", "high", "low", "average_volume_2_weeks", "average_volume", "high_52_weeks",
                "dividend_yield", "low_52_weeks", "market_cap", "pb_ratio", "pe_ratio", "shares_outstanding",
                "margin_initial_ratio", "maintenance_ratio", "day_trade_ratio", "default_collar_fraction",
                "underlying_price", "total_cash_amount", "quantity", "actual", "estimate",
            } and isinstance(data[key], str):
                data[key] = float(data[key])
            elif key in {
                "trade_value_multiplier", "year", "quarter", "ask_size", "bid_size",
                "last_trade_size", "open_interest", "volume", "float", "num_employees",
                "year_founded", "num_buy_ratings", "num_sell_ratings", "num_hold_ratings",
            } and isinstance(data[key], str):
                data[key] = int(float(data[key]))
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], (dict, list)):
                data[i] = convert_dtypes(data[i])
        return data
    return data


def filter_data(data, info):
    """Takes the data and extracts the value for the keyword that matches info.

    :param data: The data returned by request_get.
    :type data: dict or list
    :param info: The keyword to filter from the data.
    :type info: str
    :returns:  A list or string with the values that correspond to the info keyword.

    """
    none_type = None
    compare_dict = {}
    if data is None:
        return data
    elif data == [None]:
        return []
    elif isinstance(data, list):
        if len(data) == 0:
            return []
        data = convert_dtypes(data)
        compare_dict = data[0]
        none_type = []
    elif isinstance(data, dict):
        data = convert_dtypes(data)
        compare_dict = data

    if info is not None:
        if info in compare_dict and isinstance(data, list):
            return [x[info] for x in data]
        elif info in compare_dict and isinstance(data, dict):
            return data[info]
        print(error_argument_not_key_in_dictionary(info), file=get_output())
        return none_type
    return data


def inputs_to_set(inputSymbols):
    """Takes in the parameters passed to *args and puts them in a set and a list.
    The set will make sure there are no duplicates, and then the list will keep
    the original order of the input.

    :param inputSymbols: A list, dict, or tuple of stock tickers.
    :type inputSymbols: list or dict or tuple or str
    :returns:  A list of strings that have been capitalized and stripped of white space.

    """

    symbols_list = []
    symbols_set = set()

    def add_symbol(symbol):
        symbol = symbol.upper().strip()
        if symbol not in symbols_set:
            symbols_set.add(symbol)
            symbols_list.append(symbol)

    if type(inputSymbols) is str:
        add_symbol(inputSymbols)
    elif type(inputSymbols) is list or type(inputSymbols) is tuple or type(inputSymbols) is set:
        inputSymbols = [comp for comp in inputSymbols if type(comp) is str]
        for item in inputSymbols:
            add_symbol(item)

    return (symbols_list)


def request_document(url, payload=None):
    """Using a document url, makes a get request and returnes the session data.

    :param url: The url to send a get request to.
    :type url: str
    :returns: Returns the session.get() data as opppose to session.get().json() data.

    """
    try:
        res = SESSION.get(url, params=payload)
        res.raise_for_status()
    except requests.exceptions.HTTPError as message:
        print(message, file=get_output())
        return (None)

    return (res)


def request_get(url, dataType='regular', payload=None, jsonify_data=True):
    """For a given url and payload, makes a get request and returns the data.

    :param url: The url to send a get request to.
    :type url: str
    :param dataType: Determines how to filter the data. 'regular' returns the unfiltered data. \
    'results' will return data['results']. 'pagination' will return data['results'] and append it with any \
    data that is in data['next']. 'indexzero' will return data['results'][0].
    :type dataType: Optional[str]
    :param payload: Dictionary of parameters to pass to the url. Will append the requests url as url/?key1=value1&key2=value2.
    :type payload: Optional[dict]
    :param jsonify_data: If this is true, will return requests.post().json(), otherwise will return response from requests.post().
    :type jsonify_data: bool
    :returns: Returns the data from the get request. If jsonify_data=True and requests returns an http code other than <200> \
    then either '[None]' or 'None' will be returned based on what the dataType parameter was set as.

    """
    if (dataType == 'results' or dataType == 'pagination'):
        data = [None]
    else:
        data = None
    res = None
    if jsonify_data:
        try:
            res = SESSION.get(url, params=payload)
            res.raise_for_status()
            data = res.json()
        except (requests.exceptions.HTTPError, AttributeError) as message:
            print(message, file=get_output())
            return (data)
    else:
        res = SESSION.get(url, params=payload)
        return (res)
    # Only continue to filter data if jsonify_data=True, and Session.get returned status code <200>.
    if (dataType == 'results'):
        try:
            data = data['results']
        except KeyError as message:
            print("{0} is not a key in the dictionary".format(message), file=get_output())
            return ([None])
    elif (dataType == 'pagination'):
        counter = 2
        nextData = data
        try:
            data = data['results']
        except KeyError as message:
            print("{0} is not a key in the dictionary".format(message), file=get_output())
            return ([None])

        if nextData['next']:
            print('Found Additional pages.', file=get_output())
        while nextData['next']:
            try:
                res = SESSION.get(nextData['next'])
                res.raise_for_status()
                nextData = res.json()
            except:
                print('Additional pages exist but could not be loaded.', file=get_output())
                return (data)
            print('Loading page ' + str(counter) + ' ...', file=get_output())
            counter += 1
            for item in nextData['results']:
                data.append(item)
    elif (dataType == 'indexzero'):
        try:
            data = data['results'][0]
        except KeyError as message:
            print("{0} is not a key in the dictionary".format(message), file=get_output())
            return (None)
        except IndexError as message:
            return (None)

    return (data)


def request_post(url, payload=None, timeout=16, json=False, jsonify_data=True):
    """For a given url and payload, makes a post request and returns the response. Allows for responses other than 200.

    :param url: The url to send a post request to.
    :type url: str
    :param payload: Dictionary of parameters to pass to the url as url/?key1=value1&key2=value2.
    :type payload: Optional[dict]
    :param timeout: The time for the post to wait for a response. Should be slightly greater than multiples of 3.
    :type timeout: Optional[int]
    :param json: This will set the 'content-type' parameter of the session header to 'application/json'
    :type json: bool
    :param jsonify_data: If this is true, will return requests.post().json(), otherwise will return response from requests.post().
    :type jsonify_data: bool
    :returns: Returns the data from the post request.

    """
    data = None
    res = None
    try:
        if json:
            update_session('Content-Type', 'application/json')
            res = SESSION.post(url, json=payload, timeout=timeout)
            update_session(
                'Content-Type', 'application/x-www-form-urlencoded; charset=utf-8')
        else:
            res = SESSION.post(url, data=payload, timeout=timeout)
        data = res.json()
    except Exception as message:
        print("Error in request_post: {0}".format(message), file=get_output())
    # Either return response <200,401,etc.> or the data that is returned from requests.
    if jsonify_data:
        return (data)
    else:
        return (res)


def request_delete(url):
    """For a given url and payload, makes a delete request and returns the response.

    :param url: The url to send a delete request to.
    :type url: str
    :returns: Returns the data from the delete request.

    """
    try:
        res = SESSION.delete(url)
        res.raise_for_status()
        data = res
    except Exception as message:
        data = None
        print("Error in request_delete: {0}".format(message), file=get_output())

    return (data)


def update_session(key, value):
    """Updates the session header used by the requests library.

    :param key: The key value to update or add to session header.
    :type key: str
    :param value: The value that corresponds to the key.
    :type value: str
    :returns: None. Updates the session header with a value.

    """
    SESSION.headers[key] = value


def error_argument_not_key_in_dictionary(keyword):
    return ('Error: The keyword "{0}" is not a key in the dictionary.'.format(keyword))


def error_ticker_does_not_exist(ticker):
    return ('Warning: "{0}" is not a valid stock ticker. It is being ignored'.format(ticker))


def error_must_be_nonzero(keyword):
    return ('Error: The input parameter "{0}" must be an integer larger than zero and non-negative'.format(keyword))
