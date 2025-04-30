import secrets
import os
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from helpers.utils import parse_gift_list, sort_gifts, sort_names
from helpers.database_persistence import DatabasePersistence

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

@app.before_request
def load_db_and_user():
    g.storage = DatabasePersistence()
    g.user_id = session.get('user_id')

@app.route("/")
def home():
    if not g.user_id:
        return redirect(url_for('login'))
    people_gift_list = g.storage.get_all_people(g.user_id)
    sorted_people = sort_names(people_gift_list)
    return render_template('home.html', people=sorted_people)

@app.route("/<int:id>")
def person(id):
    if not g.user_id:
        return redirect(url_for('login'))
    person = g.storage.find_person(id, g.user_id)
    if not person:
        flash("Person not found.", "error")
        return redirect(url_for('home'))

    return render_template(
        'name.html',
        name=person['name'],
        gift_lst=person['gift_lst'],
        id=person['id'],
    )

@app.route("/add_person", methods=["GET", "POST"])
def add_person():
    if not g.user_id:
        return redirect(url_for('login'))
    if request.method == "POST":
        name = request.form["name"].strip()
        gift_lst = parse_gift_list(request.form["gifts"].strip())
        sorted_gifts_lst = sort_gifts(gift_lst)

        error = g.storage.validate_person(name, sorted_gifts_lst, g.user_id)
        if error:
            flash(error, "error")
            return render_template('add_person.html', name=name, gift_lst='\n'.join(sorted_gifts_lst))

        new_person = {'name': name, 'gift_lst': sorted_gifts_lst}

        person_id = g.storage.add_person(new_person, g.user_id)
        flash(f"{new_person['name']} has been created.", "success")
        return redirect(url_for('person', id=person_id))

    return render_template('add_person.html')

@app.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_person(id):
    if not g.user_id:
        return redirect(url_for('login'))
    person = g.storage.find_person(id, g.user_id)

    if not person:
        flash("Person not found.", "error")
        return redirect(url_for('home'))

    if request.method == "POST":
        new_name = request.form['name'].strip()
        gift_lst = parse_gift_list(request.form["gift_lst"].strip())

        error = g.storage.validate_person(new_name, gift_lst, g.user_id, exclude_id=id)
        if error:
            flash(error, "error")
            formatted_gift_lst = '\n'.join(person['gift_lst'])
            return render_template(
                'edit_person.html', id=id, name=person['name'], gift_lst=formatted_gift_lst
            )

        g.storage.update_person(person, new_name, gift_lst, g.user_id)
        flash(f"{new_name} has been modified.", "success")
        return redirect(url_for('person', id=id))

    formatted_gift_lst = '\n'.join(person['gift_lst'])
    return render_template('edit_person.html', id=id, name=person['name'], gift_lst=formatted_gift_lst)

@app.route("/<int:id>/delete", methods=["POST"])
def delete_person(id):
    if not g.user_id:
        return redirect(url_for('login'))
    person = g.storage.find_person(id, g.user_id)
    g.storage.delete_person(id, g.user_id)
    flash(f"{person['name']} has been deleted.", "success")
    return redirect(url_for('home'))

@app.route("/search")
def search():
    if not g.user_id:
        return redirect(url_for('login'))
    query = request.args.get('query', '')
    results = g.storage.search_matching(query, g.user_id)
    return render_template('search.html', query=query, results=results)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username:
            flash("Username is required.", "error")
            return render_template('register.html', username=username)
        if not password:
            flash("Password is required.", "error")
            return render_template('register.html', username=username)
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('register.html', username=username)

        existing_user = g.storage.get_user_by_username(username)
        if existing_user:
            flash("Username already taken. Please choose another.", "error")
            return render_template('register.html', username=username)

        user_id = g.storage.create_user(username, password)
        if user_id:
            session['user_id'] = user_id
            flash("Registration successful! You are now logged in.", "success")
            return redirect(url_for('home'))
        else:
            flash("Registration failed. Please try again.", "error")
            return render_template('register.html', username=username)
    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user_id:
        return redirect(url_for('home'))
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password']

        if not username:
            flash("Username is required.", "error")
            return render_template('login.html')
        if not password:
            flash("Password is required.", "error")
            return render_template('login.html')

        user = g.storage.get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "error")
            return render_template('login.html')
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('home'))

if __name__ == "__main__":
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)