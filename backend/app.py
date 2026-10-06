from flask import Flask

from api.errors import register_error_handlers
from api.network import network_bp

app = Flask(__name__)
register_error_handlers(app)
app.register_blueprint(network_bp)

@app.route("/health")
def health():
    return {"status": "ok"}
