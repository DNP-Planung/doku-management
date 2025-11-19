import requests, json
import trello_api_auth

def download(url):
    apiKey = trello_api_auth.apiKey
    apiToken = trello_api_auth.apiToken
    auth_header = f'OAuth oauth_consumer_key=\"{apiKey}\", oauth_token=\"{apiToken}\"'
    response = requests.get(url, headers={"Authorization": auth_header})
    return response.content

def make_url(request):
    apiKey = trello_api_auth.apiKey
    apiToken = trello_api_auth.apiToken

    # check if request already has parameters
    if '?' in request:
        return f'https://api.trello.com/1/{request}&key={apiKey}&token={apiToken}'
    else:
        return f'https://api.trello.com/1/{request}?key={apiKey}&token={apiToken}'

def get(request):
    url = make_url(request)
    contents = requests.get(url).text
    return json.loads(contents)

def post(request, data=None):
    url = make_url(request)
    contents = requests.post(url, json=data).text
    return json.loads(contents)

def put(request, data=None):
    url = make_url(request)
    contents = requests.put(url, json=data).text
    return json.loads(contents)

def delete(request):
    url = make_url(request)
    contents = requests.delete(url).text
    return json.loads(contents)
