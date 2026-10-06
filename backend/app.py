from flask import Flask

from domain.graph import Graph

app = Flask(__name__)
app.extensions["graph"] = Graph()


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
