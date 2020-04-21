from flask import Flask, render_template, request, redirect, session, flash, url_for, send_from_directory
from flask_bcrypt import Bcrypt
from datetime import datetime
import re
import os
from mysqlconnection import connectToMySQL
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "The Force Will Be With You, Always"
bcrpyt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

UPLOAD_FOLDER = 'static/videos'
ALLOWED_EXTENSIONS = {"mp4", "mov", "avi"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def main():
    mysql = connectToMySQL("uber_vidz")
    query = "SELECT videos.id_videos, videos.name, videos.pathway, videos.user_id, videos.created_at, users.first_name, users.last_name FROM videos JOIN users on videos.user_id = users.id_users ORDER BY created_at DESC;"
    all_pathways = mysql.query_db(query)

    return render_template("main.html", all_pathways = all_pathways)

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
    query = "SELECT videos.name, videos.pathway, videos.user_id, users.first_name, users.last_name FROM videos JOIN users on videos.user_id = users.id_users;"
    all_pathways = mysql.query_db(query,data)

    if result:
        return render_template("dashboard.html", user_fn = result[0], all_pathways = all_pathways)
    else:
        return render_template("login.html") 

def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_video', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Please select a file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
            mysql = connectToMySQL("uber_vidz")
            query = "INSERT into videos(pathway, name, user_id, created_at, updated_at) VALUES (%(pw)s, %(v_name)s, %(u_id)s, NOW(), NOW());"

            data = {
                "pw": filename,
                "v_name": request.form['name'],
                "u_id": session['user_id']
            }
            mysql.query_db(query, data)
            return redirect(request.url)
        
    return redirect('/landing')

@app.route('/video_page/<video_id>')
def video_page(video_id):
    mysql = connectToMySQL("uber_vidz")
    query = "SELECT videos.id_videos, videos.pathway, videos.name FROM videos WHERE videos.pathway = %(vpw)s;"
    data = {
        "vpw": video_id
    }
    specific_video = mysql.query_db(query,data)

    mysql = connectToMySQL("uber_vidz")
    query = "SELECT comments.id_comments, comments.content, comments.user_id, comments.created_at, users.first_name, users.last_name FROM comments JOIN users on comments.user_id = users.id_users ORDER BY created_at DESC;"
    all_comments = mysql.query_db(query)

    if 'user_id' not in session: 
        return render_template("video.html", all_comments = all_comments, specific_video = specific_video[0])

    mysql = connectToMySQL("uber_vidz")
    query = "SELECT users.first_name, users.last_name FROM users WHERE id_users = %(uid)s"
    data = {
        'uid': session['user_id']
    }
    result = mysql.query_db(query,data)

    mysql = connectToMySQL("uber_vidz")
    query = "SELECT comment_id FROM likes WHERE user_id = %(user_id)s"
    data = {
        'user_id': session['user_id']
    }
    results = mysql.query_db(query,data)
    liked_comments = [result['comment_id'] for result in results]

    return render_template("video.html", user_fn = result[0], all_comments = all_comments, liked_comments = liked_comments, specific_video = specific_video[0])

@app.route('/write_comment/<video_id>', methods=["POST"])
def write_comment(video_id):
    is_valid = True
    if 'user_id' not in session: 
        return redirect("/")

    if len(request.form['comment']) < 3:
        is_valid = False
        flash("Comment must be greater than 3 characters")
    if len(request.form['comment']) > 255:
        is_valid = False
        flash("Comment must be less than 255 characters")

    if is_valid:
        mysql = connectToMySQL("uber_vidz")
        query = "INSERT into comments(content, user_id, created_at, updated_at) VALUES (%(cc)s, %(u_id)s, NOW(), NOW());"

        data = {
            "cc": request.form['comment'],
            "u_id": session['user_id'],
        }
        mysql.query_db(query, data)
        
    return redirect(f"/video_page/{video_id}")

@app.route('/like_comment/<video_id>/<comment_id>')
def like_comment(video_id,comment_id):
    if 'user_id' not in session: 
        return redirect("/")

    mysql = connectToMySQL("uber_vidz")
    query = "INSERT INTO likes (user_id, comment_id, created_at, updated_at) VALUES (%(user_id)s, %(comment_id)s, NOW(), NOW());"
    data = {
        'user_id': session['user_id'],
        'comment_id': comment_id
    }
    mysql.query_db(query,data)
    return redirect(f"/video_page/{video_id}")

@app.route('/unlike_comment/<video_id>/<comment_id>')
def unlike_comment(video_id,comment_id):
    if 'user_id' not in session: 
        return redirect("/")

    mysql = connectToMySQL("uber_vidz")
    query = "DELETE FROM likes WHERE user_id = %(user_id)s AND comment_id = %(comment_id)s;"
    data = {
        'user_id': session['user_id'],
        'comment_id': comment_id
    }
    mysql.query_db(query, data)
    return redirect(f"/video_page/{video_id}")

@app.route('/contact')
def contact_us():
    return render_template("contact_us.html")

@app.route('/leave_comments', methods=["POST"])
def leave_comments():
    mysql = connectToMySQL("uber_vidz")
    query = "INSERT into feedback(first_name, last_name, email, content, created_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(fb)s, NOW());"
    
    data = {
        "fn": request.form['fname'],
        "ln": request.form['lname'],
        "em": request.form['email'],
        "fb": request.form['content'],
    }
    mysql.query_db(query,data)
    
    flash("Thank you for your feedback!")
    return redirect("/contact")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged yourself out")
    return redirect("/registration")

if __name__ == "__main__":
    app.run(debug=True)