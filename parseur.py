import requests, json
import parseur_api_key, parseur_ids

def upload(path):
    apiKey = parseur_api_key.key
    mailbox = parseur_ids.mailbox
    url = f'https://api.parseur.com/parser/{mailbox}/upload'

    files = { "file": open(path, "rb") }
    headers = { "Authorization": apiKey }

    response = requests.post(url, headers=headers, files=files)
    return json.loads(response.text)
