from flask import Flask, request, jsonify, json, abort
from random import randint
import werkzeug, traceback

app = Flask(__name__)
import db_handler as db

@app.route("/")
def test():
    """Testing if the server is online"""
    return jsonify(200)

#ger data
@app.route("/query", methods= ["POST"])
def query():
    """Returns the data requested as a json"""
    response = db.get_data(request.get_json()["range"],
                           request.get_json()["intervalMs"],
                           request.get_json()["maxDataPoints"],
                           request.get_json()["targets"],
                           request.get_json()["adhocFilters"])
    return jsonify(response)

@app.route("/search", methods= ["POST", "GET"])
def search():
    """Returns all posssible metrics"""
    response = db.get_metrics()
    return jsonify(response)

#vet inte
@app.route("/annotations", methods= ["POST"])
def annotations():
    return 200

@app.route("/init")
def init():
    db.init_db()
    return jsonify(200)
