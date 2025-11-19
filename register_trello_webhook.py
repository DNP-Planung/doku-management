import json
import trello, trello_ids, trello_api_auth

idModel = trello_ids.processing
description = "Doku Management Webhook"
callbackURL = "http://18.195.94.147/webhook/trello"

result = trello.post(f'tokens/{trello_api_auth.apiToken}/webhooks', data={
    "key": trello_api_auth.apiKey,
    "callbackURL": callbackURL,
    "idModel": idModel,
    "description": description
})
print(json.dumps(result, indent=4))
