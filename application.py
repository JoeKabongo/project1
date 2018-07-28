import os
import sys
from passlib.hash import pbkdf2_sha256
from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login users
    """
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    # check if username exist in the database
    data = db.execute("SELECT id, username, hashPassword FROM users WHERE username = :username",
                      {"username": username}).fetchall()
    if(len(data) == 0):
        message = "Such username does not exist, sorry"
        return render_template("login.html", message=message, error=True)

    # check if  the password is correct
    hashPassword = data[0][2]
    print(hashPassword)
    print(data)
    if pbkdf2_sha256.verify(password, hashPassword) is False:
        message = "Incorrect password, try again bruh!!"
        return render_template("login.html", message=message, error=True)

    # save user session id
    session["user_id"] = data[0][0]

    return redirect(url_for("index"))


@app.route("/signUp", methods=["GET", "POST"])
def signUp():
    """
    SignUp root, allow the user to create an account
    """
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    password1 = request.form.get("passwordConfirmation")

    # check if username is already taken
    database = db.execute("SELECT username  FROM users WHERE username = :username",
                          {"username": username}).fetchall()
    if len(database) >= 1:
        message = "username already taken, sorry"
        return render_template("signup.html", message=message, error=True)

    # check if email was already taken
    database = db.execute("SELECT email  FROM users WHERE email = :email",
                          {"email": email}).fetchall()
    if len(database) >= 1:
        message = "Email already taken, bruh! Sorry"
        return render_template("signup.html", message=message, error=True)

    # check if password matches
    if password != password1:
        message = "Password do not match bruh! You know better"
        return render_template("signup.html", message=message, error=True)

    # hash the password
    hash = pbkdf2_sha256.hash(password)

    db.execute("INSERT INTO users(email, username, hashPassword) VALUES(:email, :username, :hashPassword)",
               {"email": email, "username": username, "hashPassword": hash})
    db.commit()

    user_id = (db.execute("SELECT id FROM users WHERE username = :username",
                          {"username": username}).fetchall())[0]

    # save user session id
    session["user_id"] = user_id[0]
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/search", methods=["POST"])
def search():
    """ Search for a book by title, author name or isbn"""

    searchInfo = request.form.get("search")

    # find result by title
    data = (db.execute("SELECT * FROM books where title = :title",
                       {"title": searchInfo})).fetchall()

    return render_template("searchResult.html", results=data)
