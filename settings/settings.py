import base64
import requests
import pandas as pd
from pandas.io.json import json_normalize

def encodeUsernamePassword(username, password):
    """
    :param username:
    :param password:

    :return: base64 encoded string
    """

    # define how the string should be encoded
    s = username + ':' + password

    # return s as a base64 encoded string
    return base64.b64encode(s)


def invokeAuthorizationApi():
    """
    :return: access_token & user_GUID
    """

    app_token = '5fd447c8-2b45-33fc-88c4-185451f3f129'
    consumer_key = 'KPDxpF59aOBJCAAnIkqGW58gjh8a'
    consumer_secret = '3jzx1dft6VE1_EgZIjzeMekKH80a'
    stubhub_username = 'mrm9xf@gmail.com'
    stubhub_password = 'Am4122012'

    # setting up the encoded auth token
    combo = consumer_key + ':' + consumer_secret
    basic_authorization_token = base64.b64encode(combo.encode('utf-8'))

    # setting up the headers for the API call
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + basic_authorization_token.decode('utf-8')
    }

    # setting up the body
    body = {
        'grant_type': 'password',
        'username': stubhub_username,
        'password': stubhub_password,
        'scope': 'PRODUCTION'
    }

    # Making the call
    url = 'https://api.stubhub.com/login'
    r = requests.post(url, headers=headers, data=body)

    # check out
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # TODO add better error message / behavior for any known status_codes
        # let me know what the status code was on the failure and what the url attempted as
        return {
            'Errors': 'Error calling the authorization API, status_code: {}, url: {}'.format(str(r.status_code), url),
            'Results': None
        }

    token_respoonse = r.json()
    access_token = token_respoonse['access_token']
    user_GUID = r.headers['X-StubHub-User-GUID']

    return access_token, user_GUID


def invokeSearchApi(token, name=None, city=None, q=None):
    """
    function to invoke the search API given any number of optional parameters
    supported by the stubhub apis currently

    :param token
    :param name:
    :param city:
    :param q:

    :return: list of event objects
    """

    # base api url
    url = 'https://api.stubhub.com/search/catalog/events/v3?'

    # add name, if passed
    if name is not None:
        if url[-1] != '?':
            url += '&'
        url += 'name=' + str(name)

    # add city, if passed
    if city is not None:
        if url[-1] != '?':
            url += '&'
        url += 'city=' + str(city)

    # add keyword query, if passed
    if q is not None:
        if url[-1] != '?':
            url += '&'
        url += 'q=' + str(q)

    # prepare the response
    headers = {'Authorization': 'Bearer ' + token}

    # send the response
    r = requests.get(url, headers=headers)

    # check for errors
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {
            'Errors': 'Error calling the authorization API, status_code: {}, url: {}'.format(str(r.status_code), url),
            'Results': None
        }

    # load the json
    json_response = r.json()

    # return the event object
    return {'Errors': None, 'Results': json_response}



def invokeEventsApi(eventId=None):
    """
    Function to invoke the vents API so that I may pull out the metadata of the event

    :param eventId:

    :return: event object
    """

def invokeInventoryApi(token, eventId, quantity=1, minPrice=None, maxPrice=None):
    """
    function to invoke the Inventory API and return the listing information
    about the passed eventId

    :param eventId:

    :return: json response from stubhub inventory API
    """

    # prepare the API call
    url = 'https://api.stubhub.com/search/inventory/v2?'
    url += 'eventid=' + str(eventId)
    url += '&quantity=' + str(quantity)
    if minPrice is not None:
        url += '&pricemin=' + str(minPrice)

    if maxPrice is not None:
        url += '&pricemax=' + str(maxPrice)

    headers = {'Authorization': 'Bearer ' + token}

    # call the api
    r = requests.get(url, headers=headers)

    # check status code
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {
            'Errors': 'Something went wrong with the inventory API, status_code = {}, url = {}'.format(
                str(r.status_code), url
            ),
            'Results': None
        }

    # get the json
    json_response = r.json()

    return {'Errors': None, 'Results': json_response}


def processInventoryResponse(response, groupby=['sectionId', 'sectionName']):
    """
    function to take the raw response from the stubhub API and get what I want out of it

    :param response:
    :return:
    """

    # normalize it
    normalized_response = json_normalize(response)

    # take the columns I want
    cols = ['zoneId', 'zoneName', 'sectionId', 'sectionName', 'row', 'currentPrice.amount', 'quantity']
    inventory_df = normalized_response[cols]

    # execute the groupby
    grouped_df = inventory_df.groupby(groupby)

    # find minimum prices
    cols = ['currentPrice.amount']
    min_price_df = grouped_df[cols].min()
    min_price_df.columns = ['minPrice']

    # find maximum prices
    cols = ['currentPrice.amount']
    max_price_df = grouped_df[cols].max()
    max_price_df.columns = ['maxPrice']

    # find total tickets available
    cols = ['quantity']
    quantity_df = grouped_df[cols].sum()
    quantity_df.columns = ['numberOfTickets']

    # start putting them together
    final_df = min_price_df

    # merge in max
    final_df = pd.merge(final_df, max_price_df, left_index=True, right_index=True)

    # merge in quantity
    final_df = pd.merge(final_df, quantity_df, left_index=True, right_index=True)

    # reset index
    final_df = final_df.reset_index()

    # return dataframe
    return final_df

