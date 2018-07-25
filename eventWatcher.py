import json
import settings.settings as s

if __name__ == '__main__':
    # for whatever the operation, pull the access token and user guid
    (access_token, user_GUID) = s.invokeAuthorizationApi()

    # search for lollapalooza
    r = s.invokeInventoryApi(access_token, eventId=103450719)

    # check results
    if r['Results'] is not None and r['Errors'] is None:
        results = r['Results']
        listing_response = results['listing']
        listing_df = s.processInventoryResponse(listing_response)
        results = {'Errors': None, 'Results': listing_df.to_dict(orient='records')}
    else:
        results = r

    print("Content-Type: text/html\n\n")
    print(json.dumps(r))
