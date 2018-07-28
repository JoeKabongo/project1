import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# create books TABLE
db.execute('''CREATE TABLE books(id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, title VARCHAR NOT NULL,
                                 author VARCHAR NOT NULL, year INTEGER NOT NULL)''')

db.commit()

# insert books from the csv file into the database
with open("books.csv") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        isbn = row[0]
        title = row[1]
        author = row[2]
        year = int(row[3])
        db.execute("INSERT INTO books(isbn, title, author, year) VALUES(:isbn, :title, :author, :year)",
                   {"isbn": isbn, "title": title, "author": author, "year": year})
        db.commit()
