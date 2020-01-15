from flask import Flask, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from datetime import datetime
import re
from mysqlconnection import connectToMySQL

app = Flask(__name__)
app.secret_key = "The Force Will Be With You, Always"
bcrpyt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def main():
    return render_template("main.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/login')
def sign_in():
    return render_template("login.html")

@app.route('/contact')
def contact_us():
    return render_template("contact_us.html")

if __name__ == "__main__":
    app.run(debug=True)