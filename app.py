from flask import Flask, render_template, redirect, url_for, request, session, url_for, flash, jsonify
import os
from cs50 import SQL
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from helpers import login_required, allowed_file
from datetime import datetime
import pytz

# Configure an application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure directory for file uploads
app.config["UPLOAD_FOLDER"] = "./static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///socialapp.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/profile")
@login_required
def profile():
    """Display info about user"""

    # Get user_id from the url query
    id = int(request.args.get("id"))

    # Track follower users
    followed_user = False
    rows = db.execute("SELECT * FROM followers WHERE follower_id = ? AND followed_id = ?", session["user_id"], id)
    if rows:
        followed_user = True

    return render_template("profile.html", id=id, followed_user=followed_user)


@app.route("/update_profile", methods=["GET", "POST"])
@login_required
def update_profile():
    """Allow users to update their profile info"""
    id = session["user_id"]

    # Handle POST method
    # Check if a file was uploaded and if it has an allowed extension
    if request.method == "POST":

        username = request.form.get("username")
        bio = request.form.get("bio")
        profile_photo = request.files.get("profile_photo")

        # Check if neither bio nor photo is provided
        if not username and not bio and not profile_photo:
            flash("No changes were made.Please provide more information to update.")
            return redirect(url_for("update_profile"))

        # Prepare a base SQL query and params list
        query = "UPDATE users SET "
        params = []

        # Check if new username is already in use by another user
        if username:
            is_taken = db.execute("SELECT * FROM users WHERE username = ? AND id != ?", username, id)
            if is_taken:
                flash("Username already taken. Please consider another name.")
                return redirect(url_for("update_profile"))
            query += "username = ?, "
            params.append(username)


        if profile_photo:
            if not allowed_file(profile_photo.filename):
                flash("Invalid format or missing profile photo")
                return redirect(url_for("update_profile"))
            filename = secure_filename(profile_photo.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_photo.save(filepath)  # Save the file

            # Update session data to use the new profile photo
            session["profile_photo"] = filename

            query += "profile_photo = ?, "
            params.append(filename)



        if bio:
            query += "bio = ?"
            params.append(bio)

        # Remove the trailing comma and space, and add the WHERE clause
        query = query.rstrip(", ") + " WHERE id = ?"
        params.append(id)

        # Execute SQL query
        db.execute(query, *params)

        return redirect (url_for('profile', id=id))

    # Handle GET method
    return render_template("update_profile.html")


@app.route("/api/profile/<int:id>")
@login_required
def get_profile(id):
    """Fetch the user's profile from the database"""

    # Query user's data from the database
    rows = db.execute("SELECT * FROM users WHERE id = ?", id)

    # Fetch followers from the database
    followers = db.execute("SELECT COUNT(*) AS followers FROM followers WHERE followed_id = ?", id)

    # If user not found
    if len(rows) == 0:
        return jsonify({"error": "The user you are looking for is not found"}), 404

    row = rows[0]

    # Query for user's posts
    posts = db.execute("SELECT posts.id, posts.content, posts.timestamp, users.id AS user_id, users.profile_photo, users.username, (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count, (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) AS comment_count FROM posts JOIN users ON posts.user_id = users.id WHERE user_id = ? ORDER BY posts.timestamp DESC LIMIT 10", id)


    user = {
        "id": row["id"],
        "username": row["username"],
        "bio": row["bio"],
        "profile_photo": row["profile_photo"],
        "timestamp": row["timestamp"],
        "followers": followers[0]["followers"],
        "posts": posts
    }

    return jsonify(user)

@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    """Allow user to create post"""

    if request.method == "POST":

        user_id = session["user_id"]
        content = request.form.get("content")
        if not content:
            flash("Missing content")
            return redirect(url_for('create_post'))

        # Insert into posts table

        # Set Myanmar timezone
        mmt_timezone = pytz.timezone('Asia/Yangon')

        # Get the current time in Myanmar time
        local_timestamp = datetime.now(mmt_timezone).strftime('%Y-%m-%d %H:%M:%S')
        db.execute("INSERT INTO posts (user_id, content, timestamp) VALUES (?, ?, ?)", user_id, content, local_timestamp)

        return redirect(url_for('index'))
    return render_template("create_post.html")

@app.route("/api/posts", methods=["GET"])
@login_required
def get_posts():
    """Return all the posts"""
    page = int(request.args.get("page", 1))
    limit = 10
    offset = (page - 1) * limit

    # SQL query for feed with likes and comments count
    feed = db.execute("SELECT posts.id, posts.content, posts.timestamp, users.id AS user_id, users.profile_photo, users.username, (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count, (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) AS comment_count FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.timestamp DESC LIMIT ? OFFSET ?", limit, offset)

    return jsonify(feed), 200


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    """Allow user to delete user's own post"""
    user_id = session["user_id"]
    post = db.execute("SELECT * FORM posts WHERE posts.id = ? AND user_id = ?", post_id, user_id)

    if not post:
        return jsonify({"error": "post not found"}), 404

    db.execute("DELETE FROM posts WHERE id = ?", post_id)
    return jsonify({"message": "post deleted"}), 200


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Allow user to search for other users"""
    if request.method == "POST":
        username = request.form.get("username")

        if not username:
            flash("Missing username")
            return redirect(url_for('search'))

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) == 0:
            flash("Not found")
            return redirect(url_for('search'))

        return redirect(url_for('profile', id=rows[0]["id"]))
    return render_template("search.html")


@app.route("/follow")
@login_required
def follow():
    """Allow user to follow other users"""
    follower_id = session["user_id"]
    followed_id = request.args.get("id")


     # Set Myanmar timezone
    mmt_timezone = pytz.timezone('Asia/Yangon')

    # Get the current time in Myanmar time
    local_timestamp = datetime.now(mmt_timezone).strftime('%Y-%m-%d %H:%M:%S')
    # Update the followers table
    db.execute("INSERT INTO followers (follower_id, followed_id, follow_date) VALUES (?, ?, ?)", follower_id, followed_id, local_timestamp)

    return redirect(url_for('profile', id=followed_id))


@app.route("/unfollow")
@login_required
def unfollow():
    """Allow user to unfollow followed_users"""
    follower_id = session["user_id"]
    unfollowed_id = request.args.get("id")

    db.execute("DELETE FROM followers WHERE follower_id = ? AND followed_id = ?", follower_id, unfollowed_id)

    return redirect(url_for('profile', id=unfollowed_id))


@app.route("/like", methods=["POST"])
@login_required
def like():
    """Allow user to like or unlike a post"""
    user_id = session["user_id"]
    post_id = request.form.get("post_id")

    # Check if the post is already liked
    existing_like = db.execute("SELECT * FROM likes WHERE post_id = ? AND user_id = ?", post_id, user_id)

    if existing_like:
        db.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", post_id, user_id)
        flash("You unlike the post")
    else:
        mmt_timezone = pytz.timezone('Asia/Yangon')
        like_date = datetime.now(mmt_timezone).strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            "INSERT INTO likes (user_id, post_id, timestamp) VALUES (?, ?, ?)",
            user_id, post_id, like_date
        )
        flash("You liked the post.")
    return redirect(url_for('index'))


@app.route("/comment", methods=["GET", "POST"])
@login_required
def comment():
    """Allow user to comment on a post"""
    post_id = request.args.get("post_id")

    # Fetch comments
    comments = db.execute("SELECT comments.*, users.* FROM comments  JOIN users ON comments.user_id = users.id WHERE post_id = ? ORDER BY comments.timestamp DESC", post_id)

    if request.method == "POST":
        user_id = session["user_id"]
        post_id = request.form.get("post_id")
        content = request.form.get("content")

        if not content:
            flash("Comment cannot be empty.")
            return redirect(url_for('comment', post_id=post_id))

        # Insert comment into database
        db.execute(
            "INSERT INTO comments (user_id, post_id, comment_text, timestamp) VALUES (?, ?, ?, ?)",
            user_id, post_id, content, datetime.now()
        )
        flash("Comment added successfully.")

        return redirect(url_for('comment', post_id=post_id))

    return render_template("comment.html", comments=comments, post_id=post_id)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username")
            return redirect(url_for('login'))

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password")
            return redirect(url_for('login'))

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("password")
        ):
            flash("Invalid username or password")
            return redirect(url_for('login'))

        # Forget any user_id
        session.clear()

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["profile_photo"] = rows[0]["profile_photo"]

        # Redirect user to home page
        return redirect(url_for("profile", id=session["user_id"]))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Fetch form data
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    # Handle POST request
    if request.method == "POST":

        # Check if the username field is empty
        if not username:
            flash("must provide username")
            return redirect(url_for('register'))

        # Check if the password field is empty
        if not password:
            flash("must provide password")
            return redirect(url_for('register'))

        # Check if the confirmation is empty
        if not confirmation:
            flash("confirm your password")
            return redirect(url_for('register'))

        # Check if passwords match
        if password != confirmation:
            flash('passwords do not match')
            return redirect(url_for('register'))

        # Insert the new user into the database
        try:
            db.execute("INSERT INTO users (username, password_hash, timestamp) VALUES (?, ?, ?)",
                       username, generate_password_hash(password), datetime.now())
        except ValueError:  # If the username was already taken
            flash("Username is already taken")
            return redirect(url_for('register'))

        # Redirect to login page
        return redirect(url_for("login"))

    # User visits the route via GET (as by clicking the link or via redirect)
    return render_template("register.html")
