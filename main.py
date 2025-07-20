from flask import Flask, render_template, send_from_directory, jsonify
import os
import json

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/rising_stocks.json")
def rising_stocks():
    path = "rising_stocks.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    else:
        return jsonify({"results": [], "updated": "정보 없음"})

@app.route("/positive_news.json")
def positive_news():
    path = "positive_news.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    else:
        return jsonify({})

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
