from flask import Flask, request
import json, threading
from datetime import datetime
import os
import trello

app = Flask(__name__)

LOG_DIR = "webhook_logs"
os.makedirs(LOG_DIR, exist_ok=True)  # make sure logs directory exists

DOCS_DIR = "documents"
os.makedirs(DOCS_DIR, exist_ok=True)  # make sure attachments directory exists

def handle_trello_card(cardId):
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


@app.route("/webhook/trello", methods=["POST", "GET"])
def trello_webhook():
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
