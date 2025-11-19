from flask import Flask, request
import json
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "webhook_log.jsonl"   # JSON-lines format (one JSON object per line)

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    # Prepare log entry
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": request.method,
        "headers": dict(request.headers),
        "args": request.args.to_dict(),
        "body": request.get_data(as_text=True),
        "json": None
    }

    # Try to parse JSON if available
    try:
        entry["json"] = request.get_json(silent=True)
    except:
        pass

    # Append to log file
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
