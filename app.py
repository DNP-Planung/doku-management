from flask import Flask, request
import json
from datetime import datetime
import os

app = Flask(__name__)

LOG_DIR = "webhook_logs"
os.makedirs(LOG_DIR, exist_ok=True)  # make sure logs directory exists

@app.route("/webhook/<service_name>", methods=["POST", "GET"])
def webhook(service_name):
    """
    Handles webhook requests for any service dynamically.
    Logs each request into a separate file per service.
    """
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
