import os

from flask import Flask

from api.connections import connections_bp
from api.errors import register_error_handlers
from api.network import network_bp
from api.points import points_bp
from domain.graph import Graph
from seed import seed_network

app = Flask(__name__)
graph = Graph()
if os.environ.get("SEED_NETWORK") == "1":
    seed_network(graph)
app.extensions["graph"] = graph
register_error_handlers(app)
app.register_blueprint(points_bp)
app.register_blueprint(connections_bp)
app.register_blueprint(network_bp)


@app.route("/health")
def health():
    return {"status": "ok"}
