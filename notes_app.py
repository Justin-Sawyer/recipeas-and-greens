
"""
@app.route("/delete_account/<user_id>")
def delete_account(user_id):
    # user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    # user = mongo.db.users.find_one({"username": session["user"]})
    # pull = {"$pull": {"favourite_of": user}}
    # mongo.db.recipes.updateMany({}, pull)
    ""recipes = mongo.db.recipes.find()
    recipes.updateMany(
        {"$pull": {"favourite_of": session["user"]}})""
    
    # mongo.db.users.remove({"username": session["user"]})
    # favourites = mongo.db.recipes.find_one({"favourite_of": session["user"]})
    # print(favourites)
    # if existing_favourites:
        # existing_favourites.remove_one(
    #       {"favourite_of": session["user"]})
    # recipes = mongo.db.recipes.find()
    # recipes.remove({"favourite_of": session["user"]})
    # username = mongo.db.users.find_one(
    #    {"username": session["user"]})["username"]
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    print(user)
    mongo.db.recipes.update(
        {},
        {"$pull": {"favourite_of": user}})
    session.pop("user")
    # flash("Account Successfully Deleted")
    return redirect(url_for("get_recipes"))"""


@app.route("/delete_account/<user_id>")
def delete_account(user_id, recipe_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    print(user)
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})

    """ This deletes the whole account: """
    # mongo.db.users.remove({"_id": ObjectId(user_id)})
    # flash("Account Successfully Deleted")

    """ This removes the cookie: """
    # session.pop("user")

    """ This finds all recipes that session["user”] has favourited """
    for all in mongo.db.recipes.find({"favourite_of": "dhsqjkqh"}):
        print(all)
    for all in mongo.db.recipes.find({"favourite_of": user}):
        print(all)
    
    favourite_recipes = mongo.db.recipes.find({"favourite_of": "dhsqjkqh"})
    print(favourite_recipes)

    pulled_values = {"$pull": {"favourite_of": "dhsqjkqh"}}
    """ AttributeError: 'Cursor' object has no attribute 'updateMany' """
    # favourite_recipes.updateMany(pulled_values)
    """ TypeError: 'Collection' object is not callable. 
    If you meant to call the 'updateMany' method on a 'Collection' object it is failing because no such method exists."""
    # mongo.db.recipes.updateMany(pulled_values)
    return redirect(url_for("get_recipes"))




# Delete account and favourites only
@app.route("/remove_all_from_favourites_and_delete_account")
def remove_all_from_favourites_and_delete_account():
    user = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    """recipe = mongo.db.recipes.find_one(
        {"_id": ObjectId(recipe_id)})"""
    # return render_template("profile.html", user=user, recipe=recipe)
    """
    mongo.db.recipes.update_many(
        {"_id": ObjectId(recipe_id)},
        {"$pull": {"favourite_of": user}})
    for all in mongo.db.recipes.find({"_id": ObjectId(recipe_id)}):
        mongo.db.recipes.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$pull": {"favourite_of": user}})
    flash("Recipea removed from your list of favourites!")"""
    recipes = mongo.db.recipes
    myquery = {"favourite_of": user}
    newvalues = {"$pull": {"favourite_of": user}}
    recipes.update_many(myquery, newvalues)
    #for all in recipes.find()
    return redirect(url_for("get_recipes"))
