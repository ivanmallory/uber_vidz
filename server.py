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

@app.route('/registration')
def sign_in():
    return render_template("login.html")

@app.route('/create_user', methods=['POST'])
def create_user():
    is_valid = True
    
    if len(request.form['fname']) < 1:
        is_valid = False
        flash("Please enter a valid first name")
    
    if len(request.form['lname']) < 1:
        is_valid = False
        flash("Please enter a valid last name")
    
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid email address")
    
    if len(request.form['pass']) < 5:
        is_valid = False
        flash("Password Must Be At Least 5 Characters")
    
    if request.form['cpass'] != request.form ['pass']:
        is_valid = False
        flash("Incorrect Password")
    
    if not request.form['fname'].isalpha():
        is_valid = False
        flash("First name can only contain alphabetic characters")
    
    if not request.form['lname'].isalpha():
        is_valid = False
        flash("Last name can only contain alphabetic characters")
    
    if not any(char.isdigit() for char in request.form['pass']): 
        is_valid = False
        flash('Password should have at least one numeral') 
    
    if not any(char.isupper() for char in request.form['pass']): 
        is_valid = False
        flash('Password should have at least one uppercase letter') 
    
    if not any(char.islower() for char in request.form['pass']): 
        is_valid = False
        flash('Password should have at least one lowercase letter') 
    
    
    mysql = connectToMySQL("uber_vidz")
    validate_email_query = 'SELECT id_users FROM users WHERE email=%(email)s;'
    form_data = {
        'email': request.form['email']
    }
    existing_users = mysql.query_db(validate_email_query, form_data)

    if existing_users:
        is_valid = False
        flash("Email already in use")
    
    if not is_valid:
        return redirect("/registration")

    if is_valid:
        mysql = connectToMySQL("uber_vidz")
        pw_hash = bcrpyt.generate_password_hash(request.form['pass'])
        query = "INSERT into users(first_name, last_name, email, password, created_at, updated_at) VALUES (%(fname)s, %(lname)s, %(email)s, %(password_hash)s, NOW(), NOW());"

        data = {
            "fname": request.form['fname'],
            "lname": request.form['lname'],
            "email": request.form['email'],
            "password_hash": pw_hash
        }
        result_id = mysql.query_db(query, data)
        flash("Successfully added:{}".format(result_id))
        return redirect("/landing")
    return redirect("/registration")

@app.route('/login', methods=['POST'])
def login():
    mysql = connectToMySQL("uber_vidz")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email": request.form['email'] }
    result = mysql.query_db(query,data)
    if result: 
        if bcrpyt.check_password_hash(result[0]['password'], request.form['pass']):
            session['user_id'] = result[0]['id_users']
            return redirect("/landing")
    flash("You could not be logged in")
    return redirect("/login")

@app.route('/landing')
def dashboard_page():
    if 'user_id' not in session: 
        return redirect("/registration")

    mysql = connectToMySQL("uber_vidz")
    query = "SELECT users.first_name, users.last_name FROM users WHERE id_users = %(uid)s"
    data = {
        'uid': session['user_id']
    }
    result = mysql.query_db(query,data)

    mysql = connectToMySQL("uber_vidz")
    query = "SELECT videos.user_id, videos.id_videos, videos.content, videos.creator_name, videos.created_at, videos.updated_at, users.first_name, users.last_name FROM videos JOIN users on videos.user_id = users.id_users ORDER BY created_at DESC;"
    all_videos = mysql.query_db(query)

    if result:
        return render_template("dashboard.html", user_fn = result[0], all_videos = all_videos)
    else:
        return render_template("dashboard.html") 
    return render_template("dashboard.html")

@app.route('/contact')
def contact_us():
    return render_template("contact_us.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged yourself out")
    return redirect("/registration")

if __name__ == "__main__":
    app.run(debug=True)