from flask import Flask, jsonify, render_template
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/positive_news.json')
def positive_news():
    return app.send_static_file("positive_news.json")

@app.route('/rising_stocks.json')
def rising_stocks():
    return app.send_static_file("rising_stocks.json")

if __name__ == '__main__':
    app.run(debug=True)
