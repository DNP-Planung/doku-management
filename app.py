from flask import Flask, request, abort
import json, threading
from datetime import datetime
import os, ipaddress
import trello, trello_ids, parseur

app = Flask(__name__)

DOCS_DIR = "documents"
os.makedirs(DOCS_DIR, exist_ok=True)  # make sure attachments directory exists

PROCESSED_DOCS_PATH = "processed_documents.json"
# create processed docs file if it doesn't exist
if not os.path.exists(PROCESSED_DOCS_PATH):
    with open(PROCESSED_DOCS_PATH, "w") as f:
        json.dump({}, f)
processed_docs = json.load(open(PROCESSED_DOCS_PATH, "r"))

def save_processed_docs():
    with open(PROCESSED_DOCS_PATH, "w") as f:
        json.dump(processed_docs, f)

def update_custom_fields(cardId, nr, total):
    data = []

    def add_custom_field(field_id, data_type, value):
        data.append({
            'idCustomField': field_id,
            'value': {data_type: str(value)}
        })

    add_custom_field(trello_ids.customFieldId_nr, 'text', nr)
    add_custom_field(trello_ids.customFieldId_total, 'text', total)

    data = { 'customFieldItems': data }
    return trello.put(f'cards/{cardId}/customFields', data=data)

def handle_trello_card(card):
    cardId = card['id']
    if cardId in processed_docs:
        return  # already processed

    # get the first attachment
    attachments = trello.get(f"cards/{cardId}/attachments")
    if not attachments or len(attachments) == 0:
        return

    attachment = attachments[0]
    fileName = attachment['fileName']
    attachmentId = attachment['id']
    document = f"{cardId}_{attachmentId}_{fileName}"

    destination = os.path.join(DOCS_DIR, document)
    if os.path.exists(destination):
        return  # already downloaded

    # download the file
    contents = trello.download(attachment['url'])
    with open(destination, "wb") as f:
        f.write(contents)

    # mark as processed
    processed_docs[cardId] = {
        "attachmentId": attachmentId,
        "fileName": fileName,
    }
    save_processed_docs()

    result = parseur.upload(destination, cardId)
    if 'attachments' in result:
        parseurId = result['attachments']['DocumentID']
        processed_docs[cardId]['parseurId'] = parseurId
        save_processed_docs()

# Trello webhooks always come from this subnet
AUTHORIZED_SUBNET = ipaddress.ip_network("104.192.142.240/28")

@app.route("/webhook/trello", methods=["POST", "GET"])
def trello_webhook():
    sender_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    sender_ip = sender_ip.split(",")[0].strip()

    if ipaddress.ip_address(sender_ip) not in AUTHORIZED_SUBNET:
        abort(403)

    # get the card
    payload = request.get_json(silent=True)
    if not payload or 'action' not in payload:
        return {"status": "no action"}, 400

    action_data = payload['action']['data']
    if not 'card' in action_data:
        return {"status": "no card"}, 400
    card = action_data['card']

    # handle card in new thread
    threading.Thread(target=handle_trello_card, args=(card,)).start()

    # Immediately return OK to the caller
    return {"status": "ok"}, 200

def handle_parseur_result(payload):
    cardId = payload['card_id']

    # get the card
    card = trello.get(f"cards/{cardId}")
    if not card:
        return

    vendor_name = payload.get('VendorName', '')
    name = card.get('name', '')
    name = f'{name} - {vendor_name}'

    total = payload.get('TotalAmount', '')
    due_date = payload.get('InvoiceIssueDate', '')

    # update the Trello card
    trello.put(f"cards/{cardId}", data={"name": name, "due": due_date})
    update_custom_fields(cardId, nr=vendor_name, total=total)

    # move it to "Processed" list
    processed_list_id = trello_ids.outbox
    trello.put(f"cards/{cardId}", data={"idList": processed_list_id})


@app.route("/webhook/parseur", methods=["POST", "GET"])
def webhook_parseur():
    auth_header = request.headers.get('X-Authorization')
    if not parseur.verify_auth_header(auth_header):
        return {"status": "wrong auth header"}, 403

    payload = request.get_json(silent=True)
    if not payload or 'card_id' not in payload:
        return {"status": "no card_id"}, 400

    # handle card in new thread
    threading.Thread(target=handle_parseur_result, args=(payload,)).start()
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
