import os
import sys
import requests
from passlib.hash import pbkdf2_sha256
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_jsglue import JSGlue



app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False




# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"), pool_size=20, max_overflow=-1)
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
        message = "Such username can't be found in our records, sorry!"
        return render_template("login.html", message=message, error=True)

    # check if  the password is correct
    hashPassword = data[0][2]
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
    """
        Log user out.
    """

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/search", methods=["POST"])
def search():
    """
        Search for a book by title, author name or isbn
    """

    searchInfo = request.form.get("search").lower()

    # find result by title
    titles = (db.execute("SELECT id, isbn, title, author, year FROM books WHERE LOWER(title) LIKE :searchInfo",
                         {"searchInfo": "%" + searchInfo + "%"})).fetchall()

    # find result by author name
    authors = (db.execute("SELECT id, isbn, title, author, year FROM books WHERE LOWER(author) LIKE :searchInfo",
                          {"searchInfo": "%" + searchInfo + "%"})).fetchall()

    # find result by isbn
    isbn = (db.execute("SELECT id , isbn, title, author, year FROM books WHERE LOWER(isbn) LIKE :searchInfo",
                       {"searchInfo": "%" + searchInfo + "%"})).fetchall()

    return render_template("searchResult.html", titles=titles, authors=authors, isbn=isbn, searchInfo=searchInfo)


@app.route("/search_by_isbn", methods=["POST"])
def search_by_isbn():
    """
        Search book only by isbn
    """

    search_info = request.form.get("isbn")
    results = (db.execute("SELECT id , isbn, title, author, year FROM books WHERE LOWER(isbn) LIKE :isbn",
            {"isbn": "%" + search_info + "%"})).fetchall()
    return render_template("searchResult.html", results = results, searchInfo= search_info, byCategory="isbn")



@app.route("/search_by_title", methods=["POST"])
def search_by_title():
    """
        Search book only by title
    """
    search_info = request.form.get("book_title").lower()
    results = (db.execute("SELECT id, isbn, title, author, year FROM books WHERE LOWER(title) LIKE :title",
              {"title": "%" + search_info + "%"})).fetchall()
    return render_template("searchResult.html", results = results, searchInfo= search_info, byCategory="book title")



@app.route("/search_by_author", methods=["POST"])
def search_by_author():
    """
        Search book only by author name
    """
    search_info = request.form.get("author").strip()
    results = (db.execute("SELECT id, isbn, title, author, year FROM books WHERE LOWER(author) LIKE :author",
                          {"author": "%" + search_info + "%"})).fetchall()
    return render_template("searchResult.html", results = results, searchInfo= search_info, byCategory="author name")




@app.route("/bookpage/<title>, <author>, <id>, <isbn>")
def book_page(title, author, id, isbn):
    """
        return book page with book informations
    """
    id = id
    author = author
    title=title
    isbn=isbn

    #get information of the book in the database
    bookInfo = (db.execute("SELECT isbn, year FROM books WHERE id = :id", {"id": id})).fetchall()[0]
    isbn = bookInfo[0]
    year = bookInfo[1]

    #get all the reviews submitted by users of this book
    reviews =(db.execute("SELECT username, content, stars FROM reviews JOIN users ON reviews.user_id =  users.id WHERE book_id = :id AND user_id<> :user_id" ,
                        {"id":id, "user_id":session["user_id"]})).fetchall()


    #get average rating and total ratings of the book
    ratings = (db.execute("SELECT AVG(stars), COUNT(stars) FROM reviews WHERE book_id = :id", {"id":id})).fetchall()
    number_ratings = ratings[0][1]
    average_ratings= ratings[0][0]

    #save current book informations in the session
    session["book_id"] = int(id)
    session["book_title"] = title
    session["book_author"] = author
    session["isbn"] = isbn

    #check if the user already submitted a review for this book
    userReview = (db.execute("SELECT stars,content FROM reviews  WHERE book_id = :book_id AND user_id= :user_id ",
                    {"book_id":session["book_id"], "user_id":session["user_id"]})).fetchall()
    canSubmitReview = len(userReview) == 0

    if not canSubmitReview:
        user_rating = userReview[0][0]
        user_review = userReview[0][1]
        userReview = {"rating":user_rating, "review":user_review}

    else:
        userReview = {"rating":None, "review":None}

    #check if the book is in the user list of books
    favBook = db.execute("SELECT favoritebooks_id FROM users WHERE id=:id",
                          {"id":session["user_id"]}).fetchall()[0][0]

    if favBook == None:
        isFavBook = False
    else:
        isFavBook = session["book_id"] in favBook

    #get reviews and ratings info of the good from goodread api
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "k1L45BzwtDGQRQmnXw4w", "isbns": isbn})
    json = res.json()["books"]

    otherRatings = ""
    for review in reviews:
        otherRatings +=","
        otherRatings += str(review[2])

    return render_template("bookpage.html", title=title, author=author,
                          isbn=isbn, publicationYear=year, reviews=reviews,
                          canSubmitReview=canSubmitReview, userReview=userReview, json=res.json()["books"],
                          isFavBook=isFavBook, id=session["book_id"], numberRatings=number_ratings, averageRatings=average_ratings, otherRatings=otherRatings)


@app.route("/submitReview", methods=["POST"])
def submit_review():
    """
        Submit a review
    """
    review = request.form.get("review")
    rating = request.form.get("rating")

    print(f"review : {review}")
    print(f"rating: {rating}")



    db.execute("INSERT INTO reviews(user_id, book_id, content, stars)VALUES(:user_id, :book_id, :content, :stars)",
                {"user_id":session["user_id"], "book_id": session["book_id"], "content":review, "stars":rating})
    db.commit()

    return jsonify({"review":review, "rating":rating})



@app.route("/api/<isbn>")
def book_api(isbn):
    """
        return a json object of a book base on the isbn
    """
    #get the book info
    book = (db.execute("SELECT title, author, year, isbn, id FROM books WHERE isbn=:isbn",
                       {"isbn":isbn}).fetchall())

    #check if the isbn is valid
    if len(book) == 0:
        return jsonify({"error":"invalid isbn "}), 404

    book = book[0]
    title = book[0]
    author = book[1]
    year = book[2]
    isbn = book[3]
    id = book[4]

    #get the number of reviews of this book on my website
    r = (db.execute("SELECT SUM(stars), AVG(stars) FROM reviews WHERE book_id=:id", {"id":id})).fetchall()[0]
    if  r[0] == None:
        review_count = 0
        average_score = "No rating yet"
    else:
        review_count = r[0]
        average_score=r[1]


    return jsonify({
            "title": title,
            "author": author,
            "year": year,
            "isbn": isbn,
            "review_count": review_count,
            "average_score": average_score
    })


@app.route("/add_book/<id>")
def add_book(id):
    """
        add the book to the user list
    """
    id = int(id)
    #check if the book is in the user list of books
    favBook = db.execute("SELECT favoritebooks_id FROM users WHERE id=:id",
                          {"id":session["user_id"]}).fetchall()[0][0]

    if favBook == None:
        isFavBook = False
    else:
        isFavBook = session["book_id"] in favBook

    if not isFavBook:
        db.execute("UPDATE users SET favoritebooks_id=favoritebooks_id || '{:book_id}' WHERE id=:id",
                    {"book_id":id,"id":session["user_id"]})
        db.commit()

    return redirect(url_for("user_book", title=session["book_title"], author= session["book_author"],id=session["book_id"], isbn=session["isbn"]))


@app.route("/remove_book/<id>")
def remove_book(id):
    """
        Remove form list of book
    """
    id = id
    db.execute("UPDATE users SET favoritebooks_id=array_remove(favoritebooks_id, ':book_id')  WHERE id=:id",
                {"book_id":int(id),"id":session["user_id"]})
    db.commit()

    return redirect(url_for("user_book", title=session["book_title"], author= session["book_author"],id=session["book_id"], isbn=session["isbn"]))




@app.route("/profile")
def profile():
    """
        Go to the user profile page
    """

    user = (db.execute("SELECT email, username FROM users WHERE id=:id",
                      {"id":session["user_id"]})).fetchall()
    return render_template("userProfile.html", user=user)



@app.route("/mybooks")
def user_book():
    """
        Return a page with all the books that the user added to his list
    """

    books = (db.execute("SELECT favoritebooks_id FROM users WHERE id=:id",
            {"id":session["user_id"]})).fetchall()[0][0]

    my_list = []
    for id in books:
        book = (db.execute("SELECT * FROM books WHERE id=:id",
                {"id":id})).fetchall()[0]
        my_list.append(book)

    return render_template("userBook.html", books=my_list)

@app.route("/update_password", methods=["GET", "POST"])
def update_password():
    """
        Allow the user to update their password
    """
    if request.method == "GET":
        return render_template("updatePassword.html")

    #check if the user entered the is correct current password
    #if not correct return webpage with a error message
    current_password = request.form.get("current_password")
    hash_password = (db.execute("SELECT hashpassword FROM users WHERE id=:id",
                    {"id":session["user_id"]})).fetchall()
    hash_password = hash_password[0][0]
    if pbkdf2_sha256.verify(current_password, hash_password) is False:
        message = "Your current password was incorrect, try again"
        return render_template("updatePassword.html", message=message, error=True)

    #check if the new passwords matches
    new_password = request.form.get("new_password")
    password_confirmation = request.form.get("password_confirmation")
    print(f"new password {new_password}")
    print(f"password con {password_confirmation}")
    if new_password != password_confirmation:
        message = "Your new passwords did not match, try again"
        return render_template("updatePassword.html", message=message, error=True)

    #check if the new passoword is the same as the old one
    if pbkdf2_sha256.verify(new_password, hash_password) is True:
        message = "Your new password is the same as the old one"
        return render_template("updatePassword.html", message=message, error=True)


    #update the password of the user in the databse
    hash = pbkdf2_sha256.hash(new_password)
    db.execute("UPDATE users SET hashpassword=:hash WHERE id=:id",{"hash" : hash, "id":session["user_id"]})
    db.commit()
    message = "Your password has been updated"
    return render_template("updatePassword.html", message=message, success=True)


@app.route("/update_username", methods=["GET", "POST"])
def update_username():
    """
        Allow user to update their username
    """
    if request.method == "GET":
        return render_template("updateUsername.html")

    new_username = request.form.get("new_username")
    password = request.form.get("password")

    #check if username has already been taken
    check = (db.execute("SELECT id FROM users Where username = :username",
             {"username":new_username})).fetchall()
    if len(check) > 0:
        check = check[0]

        #if the user entered their own username
        if check[0] == session["user_id"]:
            message = "Bro, this is your username"
            return render_template("updateUsername.html", message=message, error=True)
        else: #if they entered someone else Username
            message = "This username has already been taking"
            return render_template("updateUsername.html", message=message, error=True)

    #if the user password is Incorrect
    hash_password =(db.execute("SELECT hashpassword FROM users WHERE id = :id",
                    {"id":session["user_id"]})).fetchall()[0][0]
    if pbkdf2_sha256.verify(password, hash_password) is False:
        message = "Incorrect password, try again!"
        return render_template("updateUsername.html", message=message, error=True)

    #update username if everything went well which mean it passsed all test above
    db.execute("UPDATE users SET username=:username WHERE id=:id",{"username" : new_username, "id":session["user_id"]})
    db.commit()
    message = "Your username has been updated"
    return render_template("updateUsername.html", message=message, success=True)


@app.route("/update_email", methods=["GET", "POST"])
def update_email():
    """
        Allow user to update their email address
    """
    if request.method == "GET":
        return render_template("updateEmail.html")
    new_email = request.form.get("new_email")
    password = request.form.get("password")

    #check if email has already been taken
    check = (db.execute("SELECT id FROM users Where email = :email",
             {"email":new_email})).fetchall()
    if len(check) > 0:
        check = check[0]

        #if the user entered their own email
        if check[0] == session["user_id"]:
            message = "Bro, this is your email"
            return render_template("updateUsername.html", message=message, error=True)
        else: #if they entered someone else Username
            message = "This email has already been taking"
            return render_template("updateEmail.html", message=message, error=True)

    #if the user password is Incorrect
    hash_password =(db.execute("SELECT hashpassword FROM users WHERE id = :id",
                    {"id":session["user_id"]})).fetchall()[0][0]
    if pbkdf2_sha256.verify(password, hash_password) is False:
        message = "Incorrect password, try again!"
        return render_template("updateEmail.html", message=message, error=True)

    #update email if everything went well which mean it passsed all test above
    db.execute("UPDATE users SET email=:email WHERE id=:id",{"email" : new_email, "id":session["user_id"]})
    db.commit()
    message = "Your email has been updated"
    return render_template("updateEmail.html", message=message, success=True)
