import requests

def kraken_public_request(uri_path, query_parameters={}):
    url = 'https://api.kraken.com' + uri_path

    if query_parameters != {}:
        url += '?'
        key_count = 0
        for key in query_parameters.keys():
            if key_count != 0:
                url += '&'
            
            url += f"{key}={query_parameters[key]}"
            key_count += 1
    
    response = requests.get(url)
    return response