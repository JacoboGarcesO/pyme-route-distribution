from flask import Flask

from api.errors import register_error_handlers

app = Flask(__name__)
register_error_handlers(app)

@app.route("/health")
def health():
    return {"status": "ok"}
