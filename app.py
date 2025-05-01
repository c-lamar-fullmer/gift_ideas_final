# app.py
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
    abort,
)
from werkzeug.security import check_password_hash
import math

from helpers.utils import parse_gift_list, sort_gifts, sort_names
from helpers.database_persistence import DatabasePersistence

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
GIFTS_PER_PAGE = 8

@app.before_request
def load_db_and_user():
    g.storage = DatabasePersistence()
    g.user_id = session.get('user_id')

@app.route("/", defaults={'page': 1})
@app.route("/page/<int:page>")
def home(page):
    if not g.user_id:
        return redirect(url_for('login'))

    total_people = g.storage.get_person_count(g.user_id)
    per_page = g.storage.ITEMS_PER_PAGE
    total_pages = math.ceil(total_people / per_page)

    if page < 1 or page > total_pages if total_pages > 0 else page != 1:
        abort(404)

    people = g.storage.get_paginated_people(g.user_id, page)
    sorted_people = sort_names(people)

    return render_template('home.html', people=sorted_people, page=page, total_pages=total_pages)

@app.route("/<int:id>", defaults={'gift_page': 1})
@app.route("/<int:id>/gifts/page/<int:gift_page>")
def person(id, gift_page):
    if not g.user_id:
        return redirect(url_for('login'))
    person_data = g.storage.find_person_with_gifts(id, g.user_id, gift_page, GIFTS_PER_PAGE)
    if not person_data:
        flash("Person not found.", "error")
        return redirect(url_for('home'))

    total_gifts = g.storage.get_gift_count(id)
    total_gift_pages = math.ceil(total_gifts / GIFTS_PER_PAGE) if GIFTS_PER_PAGE > 0 else 1

    if gift_page < 1 or gift_page > total_gift_pages if total_gift_pages > 0 else gift_page != 1:
        abort(404)

    return render_template(
        'name.html',
        name=person_data.get('name'),
        gift_lst=person_data.get('paginated_gifts', []),
        id=person_data.get('id'),
        gift_page=gift_page,
        total_gift_pages=total_gift_pages
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
    
    # Use find_person_with_gifts to retrieve the person and their gifts
    person = g.storage.find_person_with_gifts(id, g.user_id, page=1, gifts_per_page=100)  # Adjust gifts_per_page as needed

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

@app.route("/search", defaults={'page': 1})
@app.route("/search/page/<int:page>")
def search(page):
    if not g.user_id:
        return redirect(url_for('login'))
    
    query = request.args.get('query', '')
    gifts_per_page = GIFTS_PER_PAGE

    # Fetch all matching results
    results_data = g.storage.search_matching_with_gifts(
        query_str=query,
        user_id=g.user_id,
    )

    results = results_data.get('results', [])
    total_gifts = sum(len(result['paginated_gifts']) for result in results)
    total_pages = math.ceil(total_gifts / gifts_per_page)

    if page < 1 or page > total_pages if total_pages > 0 else page != 1:
        abort(404)

    # Paginate the gifts
    start_index = (page - 1) * gifts_per_page
    end_index = start_index + gifts_per_page
    paginated_results = []
    current_count = 0

    for result in results:
        gifts = result['paginated_gifts']
        if current_count + len(gifts) > start_index:
            start = max(0, start_index - current_count)
            end = min(len(gifts), end_index - current_count)
            paginated_results.append({
                'id': result['id'],
                'name': result['name'],
                'paginated_gifts': gifts[start:end]
            })
        current_count += len(gifts)
        if current_count >= end_index:
            break

    return render_template(
        'search.html',
        query=query,
        results=paginated_results,
        page=page,
        total_pages=total_pages
    )

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