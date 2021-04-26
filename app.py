import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_paginate import Pagination, get_page_args
from flask_pymongo import PyMongo, pymongo
from flask_mail import Mail, Message
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

mail_settings = {"MAIL_SERVER": os.environ.get('MAIL_SERVER'),
                 "MAIL_PORT": os.environ.get('MAIL_PORT'),
                 "MAIL_USE_TLS": False,
                 "MAIL_USE_SSL": os.environ.get('MAIL_USE_SSL'),
                 "MAIL_USERNAME": os.environ.get('MAIL_USERNAME'),
                 "MAIL_PASSWORD": os.environ.get('MAIL_PASSWORD'),
                 "SECURITY_EMAIL_SENDER":
                 os.environ.get("SECURITY_EMAIL_SENDER")}

app.config.update(mail_settings)
mail = Mail(app)


# Pagination:
# https://gist.github.com/mozillazg/69fb40067ae6d80386e10e105e6803c9
def get_all_recipes(recipes, page, offset=0, per_page=10):
    offset = (page-1) * 12
    return recipes[offset: offset + per_page]


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    categories = list(mongo.db.categories.find().sort("recipe_category", 1))
    levels = list(mongo.db.level_of_difficulty.find())

    recipes = list(mongo.db.recipes.find().sort("_id", pymongo.DESCENDING))

    # Pagination:
    # https://gist.github.com/mozillazg/69fb40067ae6d80386e10e105e6803c9
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    per_page = 12
    total = len(recipes)
    pagination_recipes = get_all_recipes(recipes,
                                         page=page,
                                         offset=offset,
                                         per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='materializecss')

    return render_template("recipes.html",
                           categories=categories,
                           levels=levels,
                           recipes=pagination_recipes,
                           page=page,
                           per_page=per_page,
                           pagination=pagination,
                           title="Home")


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    categories = list(mongo.db.categories.find().sort("recipe_category", 1))
    levels = list(mongo.db.level_of_difficulty.find())
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template("search.html", recipes=recipes,
                           categories=categories, levels=levels,
                           query=query)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if username already exists in the Database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        # Check if email already exists in the Database
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if existing_email:
            flash("Email already exists")
            return redirect(url_for("register"))

        opt_in = "on" if request.form.get("opt_in") else "off"

        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password == confirm_password:
            register = {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name"),
                "username": request.form.get("username").lower(),
                "email": request.form.get("email").lower(),
                "password": generate_password_hash(
                    request.form.get("password")),
                "opt_in": opt_in,
            }
            mongo.db.users.insert_one(register)

            # Put the new user into 'session' cookie
            session["user"] = request.form.get("username").lower()
            flash("Registration successful!")
            return redirect(url_for("profile", username=session["user"]))
        else:
            flash("Passwords did not match")
            return redirect(url_for("register"))

    return render_template("register.html", title="Register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if username exists in Database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username")})

        if existing_user:
            # Ensure hashed password matches user input
            if check_password_hash(
              existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome {}" .format(request.form.get("username")))
                return redirect(url_for("profile", username=session["user"]))
            else:
                # Invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html", title="Log In")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        user = mongo.db.users.find_one({"username": session["user"]})
        recipes = mongo.db.recipes.find()
        return render_template(
            "profile.html", user=user,
            recipes=recipes)

    user = mongo.db.users.find_one({"username": session["user"]})

    # Get username for displaying user's recipes and favourites
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    recipes_created_by = list(mongo.db.recipes.find({"created_by": username}))
    favourites_of = list(mongo.db.recipes.find({"favourite_of": username}))

    recipes = list(mongo.db.recipes.find().sort("_id", pymongo.DESCENDING))

    if session["user"]:
        return render_template(
            "profile.html", user=user,
            recipes=recipes, username=username,
            recipes_created_by=recipes_created_by,
            favourites_of=favourites_of,
            title=username)

    return render_template("profile.html")


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if request.method == "POST":
        opt_in = "on" if request.form.get("opt_in") else "off"

        data = {"$set": {
            "image_url": request.form.get("profile_image_url"),
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "email": request.form.get("email"),
            "opt_in": opt_in}
            }

        mongo.db.users.update_one({"username": session["user"]}, data)

        user = mongo.db.users.find_one({"username": session["user"]})
        return redirect(url_for('profile', username=session["user"]))

    user = mongo.db.users.find_one({"username": session["user"]})

    # Get username for displaying user's recipes
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    recipes_created_by = list(mongo.db.recipes.find({"created_by": username}))

    recipes = mongo.db.recipes.find().sort("_id", pymongo.DESCENDING)

    # If session cookie exists
    if session["user"]:
        return render_template(
            "edit_profile.html", user=user,
            recipes=recipes, username=username,
            recipes_created_by=recipes_created_by,
            title="Edit Profile")

    return render_template("edit_profile.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        # Check if username exists in Database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username")})

        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")

        if existing_user:
            # Ensure hashed password matches user input
            if check_password_hash(
              existing_user["password"], request.form.get("password")):
                if new_password == confirm_new_password:
                    password = generate_password_hash(
                                request.form.get("new_password"))
                    mongo.db.users.update_one(
                        existing_user,
                        {"$set": {
                            "password": password}})
                    flash("Your password has been changed, {}" .format(
                        request.form.get("username")))
                    return redirect(url_for("profile",
                                    username=session["user"]))
                else:
                    flash("Did your passwords match?")
                    return redirect(url_for("reset_password"))
            else:
                # Invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("profile", username=session["user"]))

        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    if session["user"]:
        return render_template(
            "reset_password.html")

    return render_template("reset_password.html")


@app.route("/logout")
def logout():
    # Remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        user = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        favourite_of = [user] if request.form.get("favourite_of") else [""]

        category = {
            "recipe_category": request.form.get("recipe_category")
        }

        # Sends EACH cat in category to categories collection
        categories = category["recipe_category"].split("\r\n")

        for cat in categories:
            if cat != "":
                new_cats = {"recipe_category": cat}
                categories_collection = mongo.db.categories
                # Check if category exists in Database
                existing_category = mongo.db.categories.find_one(
                    {"recipe_category": cat})
                if not existing_category:
                    categories_collection.insert_one(new_cats)

        recipe = {
            "recipe_name": request.form.get("recipe_name"),
            "recipe_ingredients": request.form.get("recipe_ingredients"),
            "recipe_preparation": request.form.get("recipe_preparation"),
            "recipe_notes": request.form.get("recipe_notes"),
            "recipe_prep_time": request.form.get("recipe_prep_time"),
            "recipe_cooking_time": request.form.get("recipe_cooking_time"),
            "recipe_total_time": request.form.get("recipe_total_time"),
            "recipe_description": request.form.get("recipe_description"),
            "recipe_category": categories,
            "recipe_level_of_difficulty": request.form.get(
                "recipe_level_of_difficulty"),
            "recipe_servings": request.form.get("recipe_servings"),
            "image_url": request.form.get("recipe_image_url"),
            "recipe_source": request.form.get("recipe_source"),
            "created_by": session["user"],
            "favourite_of": favourite_of
        }
        mongo.db.recipes.insert(recipe)

        """ Alert users """
        recipe_name = request.form.get("recipe_name")
        level = request.form.get("recipe_level_of_difficulty")
        description = request.form.get("recipe_description")
        image = request.form.get("recipe_image_url")
        if image == "":
            image = "https://tinyurl.com/pndmxbp8"
        alert_users = "on" if request.form.get("alert_users") else "off"
        if alert_users == "on":
            recipients = list(mongo.db.users.find({}, {
                    "_id": 0, "first_name": 1, "email": 1, "opt_in": 1}))
            for recipient in recipients:
                opt_in = recipient.get("opt_in", "value")
                if opt_in == "on":
                    print(recipient)
                    email = recipient.get("email", "value")
                    name = recipient.get("first_name", "value")
                    msg = Message(f"{user} just added a Recipea!",
                                  sender='recipeasandgreens@gmail.com',
                                  recipients=[email])
                    # mail.body kept in case recipent mail is not HTML
                    mail.body = f'''Hello {name}:
The latest Recipea to be added to Recipeas And Greens is called
{recipe_name}
{image}
Its a {level} Recipea.
This is what {user} says about it:
{description}
Check it out here:
{url_for('get_recipes', _external=True)}
Sincerely,
The team at Recipeas and Greens
'''
                    msg.html = render_template("email.html",
                                               name=name,
                                               recipe_name=recipe_name,
                                               level=level,
                                               image=image,
                                               user=user,
                                               description=description)
                    mail.send(msg)
        flash("Recipea added to the Recipeas and Greens community!")
        return redirect(url_for("get_recipes"))

    level_of_difficulty = mongo.db.level_of_difficulty.find()
    servings = mongo.db.servings.find()
    return render_template(
        "add_recipe.html", level_of_difficulty=level_of_difficulty,
        servings=servings, title="Add Recipea")


@app.route("/recipe/<recipe_id>")
def recipe(recipe_id):
    categories = list(mongo.db.categories.find().sort("recipe_category", 1))
    levels = list(mongo.db.level_of_difficulty.find())
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    return render_template("recipe.html", recipe=recipe, categories=categories,
                           levels=levels, title="Recipea")


@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":

        category = {
            "recipe_category": request.form.get("recipe_category")
        }

        # Sends EACH cat in category to categories collection
        categories = category["recipe_category"].split("\r\n")

        for cat in categories:
            if cat != "":
                new_cats = {"recipe_category": cat}
                categories_collection = mongo.db.categories
                # Check if category exists in Database
                existing_category = mongo.db.categories.find_one(
                    {"recipe_category": cat})
                if not existing_category:
                    categories_collection.insert_one(new_cats)

        submit = {
            "recipe_name": request.form.get("recipe_name"),
            "recipe_ingredients": request.form.get("recipe_ingredients"),
            "recipe_preparation": request.form.get("recipe_preparation"),
            "recipe_notes": request.form.get("recipe_notes"),
            "recipe_prep_time": request.form.get("recipe_prep_time"),
            "recipe_cooking_time": request.form.get("recipe_cooking_time"),
            "recipe_total_time": request.form.get("recipe_total_time"),
            "recipe_description": request.form.get("recipe_description"),
            "recipe_category": categories,
            "recipe_level_of_difficulty": request.form.get(
                "recipe_level_of_difficulty"),
            "recipe_servings": request.form.get("recipe_servings"),
            "image_url": request.form.get("recipe_image_url"),
            "recipe_source": request.form.get("recipe_source"),
            "created_by": session["user"],
        }

        mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, submit)
        flash("Recipe successfully edited")
        return redirect(url_for('get_recipes'))

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})

    """Redirect to home page if user who did not create
    recipe tries to force edit recipe """
    recipe_created_by = mongo.db.recipes.find_one(
        {"_id": ObjectId(recipe_id)})["created_by"]
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    if username not in recipe_created_by:
        return redirect("/")

    level_of_difficulty = mongo.db.level_of_difficulty.find()
    servings = mongo.db.servings.find()
    return render_template(
        "edit_recipe.html", recipe=recipe,
        level_of_difficulty=level_of_difficulty,
        servings=servings, title="Edit Recipea")


@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Recipe Successfully Deleted")
    return redirect(url_for("get_recipes"))


@app.route("/add_to_favourites/<recipe_id>")
def add_to_favourites(recipe_id):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    mongo.db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$addToSet": {"favourite_of": username}})
    flash("Recipea added to your list of favourites!")
    return redirect(url_for("get_recipes"))


@app.route("/remove_from_favourites/<recipe_id>")
def remove_from_favourites(recipe_id):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    mongo.db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$pull": {"favourite_of": username}})
    flash("Recipea removed from your list of favourites!")
    return redirect(url_for("get_recipes"))


@app.route("/remove_all_from_favourites_and_delete_account")
def remove_all_from_favourites_and_delete_account():
    # Get user
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    # Get recipes:
    recipes = mongo.db.recipes

    # Mark favourites as no longer favourites:
    existing_favourite_of = {"favourite_of": username}
    remove_favourite_of = {"$pull": {"favourite_of": username}}
    recipes.update_many(existing_favourite_of, remove_favourite_of)

    """Re-credits all recipes created by the user as
    "created by Former Member" """
    existing_created_by = {"created_by": session["user"]}
    recredited_created_by = {"$set": {"created_by": "Former Member"}}
    recipes.update_many(existing_created_by, recredited_created_by)

    # Delete the user account
    user = mongo.db.users.find_one(
        {"username": session["user"]})["_id"]

    mongo.db.users.delete_one({"_id": ObjectId(user)})

    # This removes the cookie
    session.pop("user")

    return redirect(url_for("get_recipes"))


@app.route("/remove_all_from_favourites_and_delete_recipes_and_delete_account")
def remove_all_from_favourites_and_delete_recipes_and_delete_account():
    # This deletes all recipes favourited_by the user
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    recipes = mongo.db.recipes
    existing_favourite_of = {"favourite_of": username}
    remove_favourite_of = {"$pull": {"favourite_of": username}}
    recipes.update_many(existing_favourite_of, remove_favourite_of)

    # This deletes all recipes created by the user
    created_by = {"created_by": session["user"]}
    recipes.delete_many(created_by)

    # This deletes the user account
    user = mongo.db.users.find_one(
        {"username": session["user"]})["_id"]

    mongo.db.users.delete_one({"_id": ObjectId(user)})

    # This removes the cookie
    session.pop("user")

    return redirect(url_for("get_recipes"))


@app.route("/get_categories")
def get_categories():
    categories = mongo.db.categories.find().sort("recipe_category", 1)
    return render_template("categories.html", categories=categories,
                           title="Categories")


@app.route("/category/<category_id>")
def category(category_id):
    # Get the category in the categories collection by its ID
    category = mongo.db.categories.find_one(
        {"_id": ObjectId(category_id)})["recipe_category"]
    # Get the levels of difficulty for the search by level of difficulty
    levels = mongo.db.level_of_difficulty.find()
    """ Get the categories for the search by category and
    sorts them alphabetically button """
    categories = list(mongo.db.categories.find().sort("recipe_category", 1))
    recipes = list(mongo.db.recipes.find(
        {"recipe_category": category}).sort("_id", pymongo.DESCENDING))

    return render_template("category.html", category=category,
                           levels=levels, recipes=recipes,
                           categories=categories,
                           title="Category")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "recipe_category": request.form.get("recipe_category")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category,
                           title="Edit Category")


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("get_categories"))


@app.route("/get_difficulty_levels")
def get_difficulty_levels():
    levels = list(mongo.db.level_of_difficulty.find())
    return render_template("difficulty_levels.html", levels=levels,
                           title="Difficulty Levels")


@app.route("/level/<level_id>")
def level(level_id):

    level = mongo.db.level_of_difficulty.find_one(
        {"_id": ObjectId(level_id)})["recipe_level_of_difficulty"]

    levels = mongo.db.level_of_difficulty.find()

    categories = list(mongo.db.categories.find().sort("recipe_category", 1))

    recipes = list(mongo.db.recipes.find(
        {"recipe_level_of_difficulty": level}).sort("_id", pymongo.DESCENDING))

    return render_template("level.html", level=level,
                           recipes=recipes, levels=levels,
                           categories=categories,
                           title="Level of Difficulty")


@app.route("/edit_levels/<level_id>", methods=["GET", "POST"])
def edit_levels(level_id):
    if request.method == "POST":
        submit = {
            "recipe_level_of_difficulty": request.form.get(
                "recipe_level_of_difficulty")
        }
        mongo.db.level_of_difficulty.update(
            {"_id": ObjectId(level_id)}, submit)
        flash("Successfully Updated")
        return redirect(url_for("get_difficulty_levels"))

    level = mongo.db.level_of_difficulty.find_one({"_id": ObjectId(level_id)})
    return render_template("edit_levels.html", level=level,
                           title="Edit Level of Difficulty")


@app.route("/delete_level/<level_id>")
def delete_level(level_id):
    mongo.db.level_of_difficulty.remove({"_id": ObjectId(level_id)})
    flash("Level Successfully Deleted")
    return redirect(url_for("get_difficulty_levels"))


# credit Karina, Code Institute Slack Channel
# https://code-institute-room.slack.com/archives/C7JQY2RHC/p1611678109168400
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        with app.app_context():
            msg = Message(subject="New Email From Contact Form")
            msg.sender = request.form.get("email")
            msg.recipients = [os.environ.get('MAIL_USERNAME')]
            message = request.form.get("message")
            msg.body = f"Email From: {msg.sender} \nMessage:{message}"
            mail.send(msg)
            flash("Email Sent!")
            return redirect(url_for('get_recipes'))

    return render_template("contact.html")


@app.errorhandler(404,)
def page_not_found(e):
    categories = list(mongo.db.categories.find().sort("recipe_category", 1))
    levels = list(mongo.db.level_of_difficulty.find())
    return render_template("404.html",
                           categories=categories,
                           levels=levels), 404


@app.errorhandler(410)
def page_not_there(e):
    categories = list(mongo.db.categories.find().sort("recipe_category", 1))
    levels = list(mongo.db.level_of_difficulty.find())
    return render_template("404.html", categories=categories,
                           levels=levels), 410


@app.errorhandler(500)
def special_exception_handler(error):
    categories = list(mongo.db.categories.find().sort("recipe_category", 1))
    levels = list(mongo.db.level_of_difficulty.find())
    return render_template("500.html", categories=categories,
                           levels=levels), 500


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
