from flask import Flask, request, abort
import json, threading
from datetime import datetime
import os, ipaddress
import trello, parseur

app = Flask(__name__)

LOG_DIR = "webhook_logs"
os.makedirs(LOG_DIR, exist_ok=True)  # make sure logs directory exists

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

def handle_trello_card(cardId):
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

    result = parseur.upload(destination)
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
    cardId = action_data['card']['id']

    # handle card in new thread
    threading.Thread(target=handle_trello_card, args=(cardId,)).start()

    # Immediately return OK to the caller
    return {"status": "ok"}, 200


@app.route("/webhook/parseur", methods=["POST", "GET"])
def webhook():
    service_name = "parseur"
    log_file = os.path.join(LOG_DIR, f"{service_name}.jsonl")

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": service_name,
        "method": request.method,
        "headers": dict(request.headers),
        "args": request.args.to_dict(),
        "body": request.get_data(as_text=True),
        "json": request.get_json(silent=True)
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return {"status": "ok", "service": service_name}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
