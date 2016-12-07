from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_jsglue import JSGlue
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from datetime import datetime, timedelta
from helpers import *
from enum import Enum
from json import dumps
import os

# configure application
app = Flask(__name__)
JSGlue(app)

# generate a random secret key
app.secret_key = os.urandom(24)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# eonfigure CS50 Library to use SQLite database
db = SQL("sqlite:///kanban.db")

colors = ["blue", "green", "orange", "pink", "red"]
color_codes = ["#66a3ff", "#00cc66", "#ff9933", "#ff66ff", "#ff5050"]
weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# date and time is used for database entries and recurring cards
TODAY = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

# maintain session when browser closes
# will expire after 31 days
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route("/")
@login_required
def index():
    """
    Default landing page is the list of board if logged in,
    otherwise user will land at login page.
    """
 
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
        
        # display the user's boards
        return render_template("boards.html")
        
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")

@app.route("/add-card", methods=["GET", "POST"])
@login_required
def add_card():
    """Adds a new card to the user's board"""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # check if board is valid
        if not request.form.get("board_id") or int(request.form.get("board_id")) < 0:
            flash("I don't know what you call that, but it's not a board.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
        
        # check if user entered a title
        if not request.form.get("title"):
            flash("Wait until you've decided a title for your card. Rinse, wash, and repeat.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
            
        # check if user entered hours
        if not request.form.get("hours"):
            flash("You do realize that Hours had a default value, right? Go back give your card a number of hours worthy of Kaizen.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
        
        # insert a new card into the database
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
    
        # return the current board, which will now display the new card
        return board(request.form.get("board_id"))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        
        # return no content
        return ('', 204)
        
        
@app.route("/edit-card/<card_id>/<originating_page>" , methods=["GET", "POST"])
@login_required
def edit_card(card_id, originating_page):
    """Changes an existing card on the user's board."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        card_id = card_id
        originating_page = originating_page
        
        # check if card id is valid
        if int(card_id) < 0:
            flash("Uh oh, don't look now, but that's not a card you're holding.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
        
        # check if user entered a title
        if not request.form.get("title"):
            flash("Wait until you've decided a title for your card. Rinse, wash, and repeat.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
            
        # check if user entered hours
        if not request.form.get("hours"):
            flash("You do realize that Hours had a default value, right? Go back give your card a number of hours worthy of Kaizen.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
        
        # update the database with the changed card information
        db.execute(
            "UPDATE cards "
            "SET name = :name, description = :description, "
            "color = :color, hours = :hours, recurring = :recurring, "
            "list_items = :list_items, completion_date = :completion_date  "
            "WHERE user_id = :user_id AND "
            "card_id = :card_id", 
            user_id=session['user_id'],
            card_id=card_id,
            name=request.form.get("title"),
            description=request.form.get("description"),
            color=request.form.get("color").lower(),
            hours=float(request.form.get("hours")),
            recurring=request.form.get("recurring").lower(),
            list_items="",
            completion_date=request.form.get("completion_date"))
        
        # display the board with the changed card
        if originating_page == "board":
            return redirect(url_for("board", board_id=request.form.get("board_id")))
        else:
            return redirect(url_for("history"))
     
    # else if user reached route via GET (as by clicking a link or via redirect)  
    else:
        
        # return no content
        return ('', 204)
    
@app.route("/edit-card-column/<card_id>/<card_column>")
@login_required
def edit_card_column(card_id, card_column):
    """
    Changes just the card's column.
    Called when the card is dragged to another column.
    """
        
    card_id = card_id
    card_column = card_column
    
    # check if card id is valid
    if int(card_id) < 0:
        flash("Uh oh, don't look now, but that's not a card you're holding.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
            
    # check if column is valid
    if int(card_column) < 0 or int(card_column) > 4:
        flash("The wall is not your oyster. Keep it on the board, pal.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
    
    # update the database with the changed column.
    db.execute(
        "UPDATE cards "
        "SET column = :column "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        column=card_column)
        
    # return no content
    return ('', 204)
    
@app.route("/edit-card-collapse/<card_id>/<collapsed>")
@login_required
def edit_card_collapse(card_id, collapsed):
    """
    Update whether the panel is collapsed or expanded
    Called whenever the collapse status changes and
    allows the user's board to remain static after reloading.
    """
        
    card_id = card_id
    collapsed = collapsed
    
    # check if card id is valid
    if int(card_id) < 0:
        flash("Uh oh, don't look now, but that's not a card you're holding.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
    
    # collapse and collapse in are HTML classes used with
    # a Bootstrap collapsible panel
    if collapsed == "true":
        collapse = "collapse"
    else:
        collapse = "collapse in"
    
    # update the database with the changed collapse status
    db.execute(
        "UPDATE cards "
        "SET collapse = :collapse "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        collapse=collapse)
        
    # return no content
    return ('', 204)
    
@app.route("/delete-card/<board_id>/<card_id>/<originating_page>")
@login_required
def delete_card(board_id, card_id, originating_page):
    """Delete the card."""
        
    board_id = board_id
    card_id = card_id
    originating_page = originating_page
    
    # check if card id is valid
    if int(card_id) < 0:
        flash("Uh oh, don't look now, but that's not a card you're holding.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
        
    # check if board is valid
    if int(board_id) < 0:
        flash("I don't know what you call that, but it's not a board.")
        return redirect(url_for("board", board_id=board_id))
    
    # delete the card from the user's board
    db.execute(
        "DELETE FROM cards "
        "WHERE card_id = :card_id AND "
        "user_id = :user_id", 
        card_id=card_id,
        user_id=session['user_id'])

    # return the same board with updated cards
    # display the board with the changed card
    if originating_page == "board":
        return redirect(url_for("board", board_id=board_id))
    else:
        return redirect(url_for("history"))
    
@app.route("/insert-list-item/<board_id>/<card_id>/<location>")
@login_required
def insert_list_item(board_id, card_id, location):
    """Insert a new list item into a list card"""
    
    board_id = board_id
    card_id = card_id
    location = location
    
    # check if card id is valid
    if int(card_id) < 0:
        flash("Uh oh, don't look now, but that's not a card you're holding.")
        redirect(url_for("board", board_id=board_id))
        
    # check if board is valid
    if int(board_id) < 0:
        flash("I don't know what you call that, but it's not a board.")
        redirect(url_for("board", board_id=board_id))
        
    # check if location is valid
    if int(location) < 0:
        flash("That's not the list...that's...that's...(crunch)")
        redirect(url_for("board", board_id=board_id))
    
    # get the list items for the current card
    card = db.execute(
        "SELECT list_items "
        "FROM cards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id AND "
        "card_id = :card_id",
        user_id=session['user_id'],
        board_id=board_id,
        card_id=card_id)
        
    # check if card exists
    if len(card) != 1:
        flash("Well, this is awkward. I thought I had your card around here somewhere...")
        redirect(url_for("board", board_id=board_id))
    
    # list items are stored as CSV in the database.    
    items = card[0]["list_items"].split(",")
    
    # give new item a generic name.
    items.insert(int(location), "New Item")
    
    # the first variable should not have a comma or a 
    # blank list item will be created
    first = True
    list_items = ""
    for item in items:
        if first:
            list_items += item
            first = False
        else :
            list_items += "," + item
    
    # update the list items with the changed values
    db.execute(
        "UPDATE cards "
        "SET list_items = :list_items "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        list_items=list_items)
        
    # return the same board with updated list items
    return redirect(url_for("board", board_id=board_id))
    
@app.route("/move-list-item/<board_id>/<card_id>/<item_id>/<location>")
@login_required
def move_list_item(board_id, card_id, item_id, location):
    """Move list items to another element in the list"""
    
    board_id = board_id
    card_id = card_id
    item_id = item_id
    location = location
    
    # check if card id is valid
    if int(card_id) < 0:
        flash("Uh oh, don't look now, but that's not a card you're holding.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
        
    # check if board is valid
    if int(board_id) < 0:
        flash("I don't know what you call that, but it's not a board.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
        
    # check if the list item is valid
    if int(item_id) < 0:
        flash("I'm sorry. I'm so sorry. Your list item must have been exterminated. Allons-y!")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
    
    # don't allow user to move item to a negative element.
    if int(location) < 0:
        return ('', 204)
    
    # get the list items for the current card
    card = db.execute(
        "SELECT list_items "
        "FROM cards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id AND "
        "card_id = :card_id",
        user_id=session['user_id'],
        board_id=board_id,
        card_id=card_id)
        
    # check if card exists
    if len(card) != 1:
        flash("Well, this is awkward. I thought I had your card around here somewhere...")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
        
    # list items are stored as CSV in the database. 
    items = card[0]["list_items"].split(",")
    
    # don't allow user to move item beyond the length of the list.
    if int(location) > len(items):
        return ('', 204)
   
    # item is simultaneously removed and inserted into new location.
    items.insert(int(location), items.pop(int(item_id)))
    
    # the first variable should not have a comma or a 
    # blank list item will be created.
    first = True
    list_items = ""
    for item in items:
        if first:
            list_items += item
            first = False
        else :
            list_items += "," + item
    
    # update the list items with the changed values
    db.execute(
        "UPDATE cards "
        "SET list_items = :list_items "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        list_items=list_items)
        
    # return the same board with updated list items
    return redirect(url_for("board", board_id=board_id))
    
@app.route("/edit-list-item/<board_id>/<card_id>/<item_id>" , methods=["GET", "POST"])
@login_required
def edit_list_item(board_id, card_id, item_id):
    """Change a list item title."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        board_id = board_id
        card_id = card_id
        item_id = item_id
        
        # check if card id is valid
        if int(card_id) < 0:
            flash("Uh oh, don't look now, but that's not a card you're holding.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
            
        # check if board is valid
        if int(board_id) < 0:
            flash("I don't know what you call that, but it's not a board.")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
            
        # check if list item is valid
        if int(item_id) < 0:
            flash("I'm sorry. I'm so sorry. Your list item must have been exterminated. Allons-y!")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
        
        # get the list items for the current card
        card = db.execute(
            "SELECT list_items "
            "FROM cards "
            "WHERE user_id = :user_id AND "
            "board_id = :board_id AND "
            "card_id = :card_id",
            user_id=session['user_id'],
            board_id=board_id,
            card_id=card_id)
            
        # check if card exists
        if len(card) != 1:
            flash("Well, this is awkward. I thought I had your card around here somewhere...")
            return redirect(url_for("board", board_id=request.form.get("board_id")))
            
        # list items are stored as CSV in the database. 
        items = card[0]["list_items"].split(",")
        
        # pop was used to remove the item, rather than remove, 
        # because it has a more efficient runtime in some situations
        items.pop(int(item_id))
        
        # insert the new title into the list
        items.insert(int(item_id), request.form.get("title"))
        
        # The first variable should not have a comma or a 
        # blank list item will be created.
        first = True
        list_items = ""
        for item in items:
            if first:
                list_items += item
                first = False
            else :
                list_items += "," + item
        
        # update the list items with the changed values
        db.execute(
            "UPDATE cards "
            "SET list_items = :list_items "
            "WHERE user_id = :user_id AND "
            "board_id = :board_id AND "
            "card_id = :card_id", 
            user_id = session['user_id'],
            board_id = board_id,
            card_id = card_id,
            list_items = list_items)
        
        # return the same board with updated list items
        return redirect(url_for("board", board_id=board_id))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        
        # Return no content
        return ('', 204)
    
@app.route("/delete-list-item/<board_id>/<card_id>/<item_id>")
@login_required
def delete_list_item(board_id, card_id, item_id):
    """Delete a list item."""
    
    board_id = board_id
    card_id = card_id
    item_id = item_id
    
    # check if card id is valid
    if int(card_id) < 0:
        flash("Uh oh, don't look now, but that's not a card you're holding.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
        
    # check if board is valid
    if int(board_id) < 0:
        flash("I don't know what you call that, but it's not a board.")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
        
    # check if list item is valid
    if int(item_id) < 0:
        flash("I'm sorry. I'm so sorry. Your list item must have been exterminated. Allons-y!")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
    
    # get the list items for the current card
    card = db.execute(
        "SELECT list_items "
        "FROM cards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id AND "
        "card_id = :card_id",
        user_id=session['user_id'],
        board_id=board_id,
        card_id=card_id)
        
    # check if card exists
    if len(card) != 1:
        flash("Well, this is awkward. I thought I had your card around here somewhere...")
        return redirect(url_for("board", board_id=request.form.get("board_id")))
        
    # list items are stored as CSV in the database. 
    items = card[0]["list_items"].split(",")
   
    # pop was used to remove the item, rather than remove, 
    # because it has a more efficient runtime in some situations
    items.pop(int(item_id))
    
    # The first variable should not have a comma or a 
    # blank list item will be created.
    first = True
    list_items = ""
    for item in items:
        if first:
            list_items += item
            first = False
        else :
            list_items += "," + item
    
    # update the list items with the changed values
    db.execute(
        "UPDATE cards "
        "SET list_items = :list_items "
        "WHERE user_id = :user_id AND "
        "card_id = :card_id", 
        user_id=session['user_id'],
        card_id=card_id,
        list_items=list_items)
        
    # return the same board with updated list items
    return redirect(url_for("board", board_id=board_id))
    
@app.route("/history")
@login_required
def history():
    """Display the user's card history."""
    
    # get the user's cards
    cards = db.execute(
        "SELECT card_id, board_id, column, name, description, color, type, hours, recurring, list_items, creation_date, completion_date "
        "FROM cards "
        "WHERE user_id = :user_id",
        user_id=session['user_id'])
        
    # check if card exists
    if len(cards) < 1:
        flash("I know clean boards are nice, but I can't show you're history if you don't have any cards.")
        return render_template("history.html", cards=cards)
        
    # return the user's history
    return render_template("history.html", cards=cards)

@app.route("/analytics")
@login_required
def analytics():
    """Display charts for analyzing the user's data."""
    
    color_count_dict = {}
    color_counts = []
    creation_month_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    # get the user's username
    user = db.execute(
        "SELECT username "
        "FROM users "
        "WHERE user_id = :user_id",
        user_id=session['user_id'])
        
    # check if user exists
    if len(user) < 1:
        flash("I couldn't find you. I will call you figment.")
        return render_template("login.html")
    
    # get the user's cards
    cards = db.execute(
        "SELECT card_id, column, name, description, color, type, hours, recurring, list_items, creation_date "
        "FROM cards "
        "WHERE user_id = :user_id",
        user_id=session['user_id'])
        
    # check there are any cards
    if len(cards) < 1:
        flash("How many cards does it take to view your analytics? At least 1.")
        return redirect(url_for("boards"))
    
    # initialize the dictionary keys/values
    for color in colors:
        color_count_dict[color] = 0
    
    # get card attributes needed for charts
    for card in cards:
        
        # isolate the month from the card's creation date
        creation_date = card["creation_date"].split("-")
        month = int(creation_date[1])
        
        # the numerical month - 1 is used to indicate the array index
        creation_month_counts[month - 1] += 1
        
        # increment the corresponding dictionary value
        color_count_dict[card["color"]] += 1
        
    # dictionary values are stored in an array because
    # the chart data attribute takes an array.
    for color in color_count_dict:
        color_counts.append(color_count_dict[color])
        
    # return the user's analytics page
    return render_template("analytics.html", 
        colors=color_codes,
        number=color_counts,
        color_count_dict=color_count_dict,
        creation_date_counts=creation_month_counts,
        name=user[0]["username"])
    
@app.route("/guest")
def guest():
    """Display a playground area for guests to try features."""
 
    # get the guest board
    board = db.execute(
        "SELECT board_id, name, column_titles "
        "FROM boards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id", 
        user_id="0",
        board_id="0")
        
    # check if the board exists
    if len(board) < 1:
        flash("Sorry, I forgot I was having guests over. My board is in the wash.")
        return render_template("login.html")
        
    # get the guest card
    cards = db.execute(
        "SELECT card_id, column, name, description, color, type, hours, recurring, list_items, collapse, completion_date "
        "FROM cards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id", 
        user_id="0",
        board_id="0")
        
    # check if there are any cards
    if len(cards) > 0:
        
        for card in cards:
        
            # adding a card will result in a field of "". Manual insert will result in NULL
            if card["completion_date"] == "" or card["completion_date"] is None:
                card["completed"] = "incomplete"
            else:
                card["completed"] = "completed"
            card["list_items"]=card["list_items"].split(",")
    
    # return the guest board
    return render_template("guest.html", board=board[0], titles=board[0]["column_titles"].split(","), cards=cards)
    
@app.route("/board/<board_id>")
@login_required
def board(board_id):
    """Display the requested board"""
    
    board_id = board_id
    
    # check if board id is valid
    if int(board_id) < 0:
        flash("I don't know what you call that, but it's not a board.")
        return redirect(url_for("boards"))
    
    # get the user's board
    board = db.execute(
        "SELECT board_id, name, column_titles "
        "FROM boards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id", 
        user_id=session['user_id'],
        board_id=board_id)
        
    if len(board) != 1:
        flash("I don't know what you call that, but it's not a board.")
        return redirect(url_for("boards"))
        
    weekday = weekdays[int(datetime.today().weekday())]
        
    # get the cards for the requested board
    cards = db.execute(
        "SELECT card_id, column, name, description, color, type, hours, recurring, list_items, collapse, completion_date "
        "FROM cards "
        "WHERE user_id = :user_id AND "
        "board_id = :board_id AND "
        "(completion_date = :empty OR "
        "recurring = :daily OR "
        "recurring = :today)", 
        user_id=session['user_id'],
        board_id=board_id,
        empty="",
        daily="daily",
        today=weekday)
        
    if len(cards) > 0:
        
        for card in cards:
            
            
            
            # adding a card will result in a field of "". Manual insert will result in NULL
            if card["completion_date"] == "" or card["completion_date"] is None:
                card["completed"] = "incomplete"
            else:
                card["completed"] = "completed"
            card["list_items"]=card["list_items"].split(",")
    
    # return the request board
    return render_template("board.html", board=board[0], titles=board[0]["column_titles"].split(","), cards=cards)
    
@app.route("/boards")
@login_required
def boards():
    """Display a list of the user's boards"""
    
    # query database for stock symbols and the sum of corresponding shares
    board_rows = db.execute(
        "SELECT board_id, name, column_titles "
        "FROM boards "
        "WHERE user_id = :user_id ", 
        user_id=session['user_id'])
        
    if len(board_rows) > 0:
        
        # lookup additional stock data and add it to rows
        for board in board_rows:
            board["column_titles"] = board["column_titles"].split(",")
        
    return render_template("boards.html",boards=board_rows)
    
@app.route("/edit-board/<board_id>" , methods=["GET", "POST"])
@login_required
def edit_board(board_id):
    """Edit a board's information."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        board_id = board_id
        column_1 = str(request.form.get("col-1"))
        column_2 = str(request.form.get("col-2"))
        column_3 = str(request.form.get("col-3"))
        column_4 = str(request.form.get("col-4"))
        
        # check if board id is valid
        if int(board_id) < 0:
            flash("I don't know what you call that, but it's not a board.")
            return redirect(url_for("boards"))
        
        # update the database with the changed board information
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
    
        # return the user's list of boards
        return redirect(url_for("boards"))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else: 
        
        # return the user's list of boards
        return redirect(url_for("boards"))

@app.route("/add-board", methods=["GET", "POST"])
@login_required
def add_board():
    """Add a new board."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        column_1 = str(request.form.get("col-1"))
        column_2 = str(request.form.get("col-2"))
        column_3 = str(request.form.get("col-3"))
        column_4 = str(request.form.get("col-4"))
        
        # add a new board to the database
        db.execute(
            "INSERT INTO boards (user_id, name, number_of_columns, column_titles) "
            "VALUES(:user_id, :name, :number_of_columns, :column_titles)", 
            user_id=session["user_id"], 
            name=request.form.get("title"),
            number_of_columns=4,
            column_titles=column_1 + "," + column_2 + "," + column_3 + "," + column_4)
        
        # get the user's boards
        boards = db.execute(
            "SELECT * FROM boards "
            "WHERE user_id = :user_id", 
            user_id=session['user_id'])
            
        if len(boards) < 1:
            flash("Houston, we have a problem. Board initialization has failed, over.")
            return redirect(url_for("boards"))
            
        # the last board is the one just created
        board_id = boards[-1]["board_id"]
    
        # return the newly created board
        return redirect(url_for("board", board_id=board_id))
    
    # else if user reached route via GET (as by clicking a link or via redirect) 
    else: 
        
        # return the user's list of boards
        return redirect(url_for("boards"))
        
@app.route("/delete-board/<board_id>")
@login_required
def delete_board(board_id):
    """Delete a board."""
        
    board_id = board_id
    
    # check if board id is valid
    if int(board_id) < 0:
        flash("I don't know what you call that, but it's not a board.")
        return redirect(url_for("boards"))
    
    # delete a board from the database.
    db.execute(
        "DELETE FROM boards "
        "WHERE board_id = :board_id AND "
        "user_id = :user_id", 
        board_id=board_id,
        user_id=session['user_id'])

    # return the updated list of boards
    return redirect(url_for("boards"))