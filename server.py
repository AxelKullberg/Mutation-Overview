from flask import Flask, request, jsonify, json
import werkzeug
import json_handler as db

@app.route("/")
def test():
    """Testing if the server is online"""
    return jsonify(200)

#ger data
@app.route("/query", methods= ["POST"])
def query():
    """Returns the data requested as a json"""
    response = db.get_data(request.get_json()["maxDataPoints"],
                           request.get_json()["targets"])
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
