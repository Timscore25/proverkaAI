from flask import Flask, request, jsonify, g, render_template
import sqlite3
import requests
import json
import uuid
from db import DBConnection
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_URL = "https://api.zerogpt.com/api/detect/detectText"
API_KEY = "16549579-2073-4e51-b90a-eb947682de1f"
FREE_TOKENS = 100

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home_bg():
    return render_template("index.html")

@app.route("/gr")
def home_gr():
    return render_template("index_gr.html")

@app.route("/ro")
def home_ro():
    return render_template("index_ro.html")

@app.route("/rs")
def home_sr():
    return render_template("index_rs.html")

@app.route("/mk")
def home_mk():
    return render_template("index_mk.html")

# Add more routes as needed

@app.before_request
def assign_udid():
    user_udid = request.cookies.get('udid')
    if not user_udid:
        user_udid = str(uuid.uuid4())
        g.set_cookie = True
    else:
        g.set_cookie = False
    g.user_udid = user_udid

@app.after_request
def set_udid_cookie(response):
    if getattr(g, 'set_cookie', False):
        response.set_cookie('udid', g.user_udid, max_age=60*60*24*365)
    return response

@app.route('/detect', methods=['POST'])
def detect_text():
    request_id = str(uuid.uuid4())
    user_text = request.json.get('text', '')
    user_id = g.user_udid
    db = DBConnection()
    available_tokens = db.get_tokens(user_id)

    if available_tokens <= 0:
        return jsonify({
            "success": False,
            "message": "Token limit reached for today.",
            "tokens_left": 0
        }), 403

    payload = {
        "input_text": user_text,
        "sentences": [],
        "h": [],
        "collection_id": 0,
        "fileName": "",
        "feedback": ""
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "ApiKey": API_KEY
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        result_json = response.json()
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    db.log_request(request_id, user_id, user_text, json.dumps(result_json), result_json.get("fakePercentage", "0"))
    db.use_token(user_id)

    return jsonify({
        "success": True,
        "data": result_json.get("data", {}),
        "tokens_left": db.get_tokens(user_id),
        "request_id": request_id
    })

@app.route('/tokens', methods=['GET'])
def get_tokens():
    user_id = g.user_udid
    tokens = DBConnection().get_tokens(user_id)
    return jsonify({
        "success": True,
        "tokens_left": tokens
    })

@app.route('/<request_id>', methods=['GET'])
def get_request_by_id(request_id):
    db = DBConnection()
    request_data = db.get_request(request_id)

    if not request_data:
        return "Request not found", 404

    if isinstance(request_data, sqlite3.Row):
        request_data = dict(request_data)

    try:
        result_data = json.loads(request_data['result'])
    except:
        result_data = {}

    return render_template('individual.html',
                           request_id=request_data['request_id'],
                           text=request_data['text'],
                           result=result_data.get('data', {}))

@app.route('/recent', methods=['GET'])
def get_recent_requests():
    db = DBConnection()
    requests = db.get_recent_requests(limit=10)
    return jsonify({
        "success": True,
        "requests": requests
    })

@app.route('/usage', methods=['GET'])
def get_usage():
    db = DBConnection()
    usage = db.get_usage()
    return jsonify({
        "requests": usage
    })

@app.route('/', methods=['GET'])
def renderIndex():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)