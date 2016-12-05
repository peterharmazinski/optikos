from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_jsglue import JSGlue
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from datetime import datetime, timedelta
from helpers import *
import os

# configure application
app = Flask(__name__)
JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///kanban.db")
user_name = ""

TODAY = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

@app.route("/")
def index():
    
    # if user reached route via POST (as by submitting a form via POST)
 
    return redirect(url_for("boards"))
        
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            flash("Must enter username")
            return render_template("login.html")

        # ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        # query database for username
        user_rows = db.execute(
            "SELECT * FROM users "
            "WHERE username = :username", 
            username=request.form.get("username"))

        # ensure username exists and password is correct
        if (len(user_rows) != 1 or 
            not pwd_context.verify(request.form.get("password"), user_rows[0]["password"])):
                flash("Invalid username and/or password")
                return render_template("login.html")

        # remember which user has logged in
        session["user_id"] = user_rows[0]["user_id"]
   
        # redirect user to home page
        return redirect(url_for("boards"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
        
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            flash("Must enter username")
            return render_template("register.html")

        # ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("register.html")
            
        # query database for username
        rows = db.execute(
            "SELECT * FROM users "
            "WHERE username = :username", 
            username=request.form.get("username"))

        # check is username already exists
        if len(rows) > 0:
            flash("Usernmae already exists")
            return render_template("register.html")
            
        # ensure the passwords match
        elif request.form.get("password") != request.form.get("password_2"):
            flash("Passwords don't match")
            return render_template("register.html")

        # add user to database
        db.execute(
            "INSERT INTO users (username, password) "
            "VALUES(:username, :password)", 
            username=request.form.get("username"), 
            password=pwd_context.encrypt(request.form.get("password")))

        # query database for username
        new_user = db.execute(
            "SELECT * "
            "FROM users "
            "WHERE username = :username", 
            username=request.form.get("username"))

        # check is username already exists
        if len(new_user) != 1:
            flash("Registration failed")
            return render_template("register.html")

        # remember which user has logged in
        session["user_id"] = new_user[0]["user_id"]
        
        # create new board
        db.execute(
            "INSERT INTO boards (user_id, name, number_of_columns, column_titles) "
            "VALUES(:user_id, :name, :number_of_columns, :column_titles)", 
            user_id=session["user_id"], 
            name=request.form.get("username") + "'s Board",
            number_of_columns=4,
            column_titles="To Do,Doing,Pending,Done")

        # redirect user to home page with registered alert
        return index()

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))
    
@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change users password"""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")
        
        # ensure current was submitted
        if not request.form.get("curr_password"):
            return apology("must provide current password")

        # ensure new password was submitted
        elif not request.form.get("new_password"):
            return apology("must provide new password")
            
        # ensure the new passwords match
        elif request.form.get("new_password") != request.form.get("new_password_2"):
            return apology("new passwords don't match")
            
        # query database for username
        rows = db.execute(
            "SELECT * FROM users "
            "WHERE username = :username AND id = :id ", 
            username=request.form.get("username"),
            id=session['user_id'])
            
        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("curr_password"), rows[0]["password"]):
            return apology("invalid username and/or password")
            
        # update the user's password
        db.execute(
            "UPDATE users SET password = :password "
            "WHERE username = :username", 
            password=pwd_context.encrypt(request.form.get("new_password")), 
            username=request.form.get("username"))
        
        # display the user's transaction history
        return render_template("boards.html")
        
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")

@app.route("/add-card", methods=["GET", "POST"])
def add_card():
    """Log user in."""
    
    if request.method == "POST":
        
        db.execute(
            "INSERT INTO cards (board_id, user_id, column, name, description, color, type, hours, recurring, list_items, creation_date, completion_date) "
            "VALUES(:board_id, :user_id, :column, :name, :description, :color, :type, :hours, :recurring, :list_items, :creation_date, :completion_date)", 
            board_id=request.form.get("board_id"),
            user_id=session["user_id"], 
            column=request.form.get("column"),
            name=request.form.get("title"),
            description=request.form.get("description"),
            color=request.form.get("color").lower(),
            type=request.form.get("type").lower(),
            hours=float(request.form.get("hours")),
            recurring=request.form.get("recurring").lower(),
            list_items="list item",
            creation_date=TODAY,
            completion_date=request.form.get("completion_date"))
    
        # Return no content
        return board(request.form.get("board_id"))
        
    else:
        
        return ('', 204)
        
        
@app.route("/edit-card/<card_id>" , methods=["GET", "POST"])
def edit_card(card_id):
    """Log user in."""
    
    if request.method == "POST":
        
        card_id = card_id
        
        db.execute(
        "UPDATE cards "
        "SET name = :name, description = :description, "
        "color = :color, type = :type, hours = :hours, recurring = :recurring, "
        "list_items = :list_items, completion_date = :completion_date  "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        name=request.form.get("title"),
        description=request.form.get("description"),
        color=request.form.get("color").lower(),
        type=request.form.get("type").lower(),
        hours=float(request.form.get("hours")),
        recurring=request.form.get("recurring").lower(),
        list_items="",
        completion_date=request.form.get("completion_date"))
        
        return board(request.form.get("board_id"))
        
    else:
        
        # Return no content
        return ('', 204)
    
@app.route("/edit-card-column/<card_id>/<card_column>")
def edit_card_column(card_id, card_column):
    """Log user in."""
        
    card_id = card_id
    card_column = card_column
    
    db.execute(
        "UPDATE cards "
        "SET column = :column "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        column=card_column)
        
    # Return no content
    return ('', 204)
    
@app.route("/edit-card-collapse/<card_id>/<collapsed>")
def edit_card_collapse(card_id, collapsed):
    """Update whether the panel is collapsed or expanded"""
        
    card_id = card_id
    collapsed = collapsed
    
    # collapse and collapse in are HTML classes used with
    # a Bootstrap collapsible panel
    if collapsed == "true":
        collapse = "collapse"
    else:
        collapse = "collapse in"
    
    db.execute(
        "UPDATE cards "
        "SET collapse = :collapse "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        collapse=collapse)
        
    # Return no content
    return ('', 204)
    
@app.route("/insert-list-item/<board_id>/<card_id>/<item_id>/<location>")
def insert_list_item(board_id, card_id, item_id, location):
    """Update whether the panel is collapsed or expanded"""
    
    board_id = board_id
    card_id = card_id
    item_id = item_id
    location = location
    
    card = db.execute(
        "SELECT list_items "
        "FROM cards "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id",
        user_id=session['user_id'],
        card_id=card_id)
        
    items = card[0]["list_items"].split(",")
    
    items.insert(location, "New Item")
    
    list_items = ""
    for item in items:
        list_items += item + ","
    
    db.execute(
        "UPDATE cards "
        "SET list_items = :list_items "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        list_items=list_items)
        
    # Return no content
    return board(request.form.get("board_id"))
    
@app.route("/delete-card/<board_id>/<card_id>")
def delete_card(board_id, card_id):
    """Display user's boards"""
        
    board_id = board_id
    card_id = card_id
    
    db.execute(
        "DELETE FROM cards "
        "WHERE card_id = :card_id AND "
        "user_id = :user_id", 
        card_id=card_id,
        user_id=session['user_id'])

    # redirect user to home page
    return board(board_id)
    

    
@app.route("/history")
def history():
    """Log user in."""
    
    cards = db.execute(
        "SELECT card_id, column, name, description, color, type, hours, recurring, list_items "
        "FROM cards "
        "WHERE user_id = :user_id",
        user_id=session['user_id'])
        
    # redirect user to home page
    return render_template("history.html", cards=cards)

@app.route("/analytics")
def analytics():
    """Log user in."""
    
    # query database for stock symbols and the sum of corresponding shares
    board_rows = db.execute(
        "SELECT board_id, name, column_titles "
        "FROM boards "
        "WHERE user_id = :user_id ", 
        user_id=session['user_id'])
    
    cards = db.execute(
        "SELECT card_id, column, name, description, color, type, hours, recurring, list_items "
        "FROM cards "
        "WHERE user_id = :user_id",
        user_id=session['user_id'])
        
    # redirect user to home page
    return render_template("analytics.html")
    
@app.route("/guest")
def guest():
    """Log user in."""
        
    # redirect user to home page
    return render_template("guest.html")
    
@app.route("/board/<board_id>")
@login_required
def board(board_id):
    """Display user's boards"""
    board_id = board_id
    board = db.execute(
        "SELECT board_id, name, column_titles "
        "FROM boards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id", 
        user_id=session['user_id'],
        board_id=board_id)
        
    cards = db.execute(
        "SELECT card_id, column, name, description, color, type, hours, recurring, list_items, collapse, completion_date "
        "FROM cards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id", 
        user_id=session['user_id'],
        board_id=board_id)
        
    for card in cards:
        if card["completion_date"] == "":
            card["completed"] = "incomplete"
        else:
            card["completed"] = "completed"
        card["list_items"]=card["list_items"].split(",")
    
    # redirect user to home page
    return render_template("board.html", board=board[0], titles=board[0]["column_titles"].split(","), cards=cards)
    
@app.route("/boards")
@login_required
def boards():
    """Display user's boards"""
    
    # query database for stock symbols and the sum of corresponding shares
    board_rows = db.execute(
        "SELECT board_id, name, column_titles "
        "FROM boards "
        "WHERE user_id = :user_id ", 
        user_id=session['user_id'])
        
    # lookup additional stock data and add it to rows
    for board in board_rows:
        board["column_titles"] = board["column_titles"].split(",")
        
    return render_template("boards.html",boards=board_rows)
    
@app.route("/edit-board/<board_id>" , methods=["GET", "POST"])
def edit_board(board_id):
    """Display user's boards"""
    
    if request.method == "POST":
        
        board_id = board_id
        column_1 = str(request.form.get("col-1"))
        column_2 = str(request.form.get("col-2"))
        column_3 = str(request.form.get("col-3"))
        column_4 = str(request.form.get("col-4"))
        
        db.execute(
            "UPDATE boards "
            "SET name = :name, "
            "column_titles = :column_titles "
            "WHERE board_id = :board_id AND "
            "user_id = :user_id", 
            board_id=board_id,
            user_id=session['user_id'],
            name=request.form.get("title"),
            column_titles=column_1 + "," + column_2 + "," + column_3 + "," + column_4)
    
        # redirect user to home page
        return redirect(url_for("boards"))
        
    else: 
        
        return redirect(url_for("boards"))

@app.route("/add-board", methods=["GET", "POST"])
def add_board():
    """Display user's boards"""
    
    if request.method == "POST":
        
        column_1 = str(request.form.get("col-1"))
        column_2 = str(request.form.get("col-2"))
        column_3 = str(request.form.get("col-3"))
        column_4 = str(request.form.get("col-4"))
        
        # create new board
        db.execute(
            "INSERT INTO boards (user_id, name, number_of_columns, column_titles) "
            "VALUES(:user_id, :name, :number_of_columns, :column_titles)", 
            user_id=session["user_id"], 
            name=request.form.get("title"),
            number_of_columns=4,
            column_titles=column_1 + "," + column_2 + "," + column_3 + "," + column_4)
            
        boards = db.execute(
            "SELECT * FROM boards "
            "WHERE user_id = :user_id", 
            user_id=session['user_id'])
            
        board_id = boards[-1]["board_id"]
    
        # redirect user to home page
        return redirect(url_for("board", board_id=board_id))
        
    else: 
        
        return redirect(url_for("boards"))
        
@app.route("/delete-board/<board_id>")
def delete_board(board_id):
    """Display user's boards"""
        
    board_id = board_id
    
    db.execute(
        "DELETE FROM boards "
        "WHERE board_id = :board_id AND "
        "user_id = :user_id", 
        board_id=board_id,
        user_id=session['user_id'])

    # redirect user to home page
    return redirect(url_for("boards"))
    

        


# Generate a random secret key
app.secret_key = os.urandom(24)