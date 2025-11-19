import requests, json
import parseur_auth, parseur_ids

def upload(path, cardId):
    apiKey = parseur_auth.apiKey
    mailbox = parseur_ids.mailbox
    url = f'https://api.parseur.com/parser/{mailbox}/upload?cardId={cardId}'

    files = { "file": open(path, "rb") }
    headers = { "Authorization": apiKey }

    response = requests.post(url, headers=headers, files=files)
    return json.loads(response.text)

def verify_auth_header(header):
    return header == parseur_auth.webhookAuthKey
