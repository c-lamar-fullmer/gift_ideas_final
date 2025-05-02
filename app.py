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

# Initialize the Flask application
app = Flask(__name__)
# Set a secret key for the Flask app to enable session management and prevent CSRF attacks
app.secret_key = secrets.token_hex(32)
# Define the number of gifts to display per page
GIFTS_PER_PAGE = 8

# This function runs before each request to the application
@app.before_request
def load_db_and_user():
    # Create an instance of the DatabasePersistence class to interact with the database
    g.storage = DatabasePersistence()
    # Get the user ID from the session. 'g' is a global object for the current request.
    g.user_id = session.get('user_id')

# Route for the homepage, with optional pagination
@app.route("/", defaults={'page': 1})
@app.route("/page/<int:page>")
def home(page):
    # Redirect to login if the user is not logged in
    if not g.user_id:
        return redirect(url_for('login'))

    # Get the total number of people associated with the current user
    total_people = g.storage.get_person_count(g.user_id)
    # Get the number of items to display per page from the database persistence layer
    per_page = g.storage.ITEMS_PER_PAGE
    # Calculate the total number of pages needed for pagination
    total_pages = math.ceil(total_people / per_page)

    # Redirect to the first page if the requested page is out of bounds
    if page < 1 or (total_pages > 0 and page > total_pages):
        return redirect(url_for('home', page=1))

    # Retrieve a paginated list of people for the current user
    people = g.storage.get_paginated_people(g.user_id, page)
    # Sort the list of people by name
    sorted_people = sort_names(people)

    # Render the homepage template with the list of people, current page, and total pages
    return render_template('home.html', people=sorted_people, page=page, total_pages=total_pages)

# Route for displaying details of a specific person and their gifts, with pagination for gifts
@app.route("/<int:id>", defaults={'gift_page': 1})
@app.route("/<int:id>/gifts/page/<int:gift_page>")
def person(id, gift_page):
    # Redirect to login if the user is not logged in
    if not g.user_id:
        return redirect(url_for('login'))
    # Retrieve the person's data along with a paginated list of their gifts
    person_data = g.storage.find_person_with_gifts(id, g.user_id, gift_page, GIFTS_PER_PAGE)
    # If the person is not found, display an error message and redirect to the homepage
    if not person_data:
        flash("Person not found.", "error")
        return redirect(url_for('home'))

    # Get the total number of gifts for this person
    total_gifts = g.storage.get_gift_count(id)
    # Calculate the total number of pages needed for gift pagination
    total_gift_pages = math.ceil(total_gifts / GIFTS_PER_PAGE) if GIFTS_PER_PAGE > 0 else 1

    # Redirect to the first gift page if the requested page is out of bounds
    if gift_page < 1 or (total_gift_pages > 0 and gift_page > total_gift_pages):
        return redirect(url_for('person', id=id, gift_page=1))

    # Render the template for displaying a person's details and their gifts
    return render_template(
        'name.html',
        name=person_data.get('name'),
        gift_lst=person_data.get('paginated_gifts', []),
        id=person_data.get('id'),
        gift_page=gift_page,
        total_gift_pages=total_gift_pages
    )

# Route for adding a new person
@app.route("/add_person", methods=["GET", "POST"])
def add_person():
    # Redirect to login if the user is not logged in
    if not g.user_id:
        return redirect(url_for('login'))
    # Handle the form submission when adding a person
    if request.method == "POST":
        # Get the name and list of gifts from the form
        name = request.form["name"].strip()
        gift_lst = parse_gift_list(request.form["gifts"].strip())
        # Sort the list of gifts
        sorted_gifts_lst = sort_gifts(gift_lst)

        # Validate the person's name and gift list
        error = g.storage.validate_person(name, sorted_gifts_lst, g.user_id)
        # If there's a validation error, display it and re-render the add person form
        if error:
            flash(error, "error")
            return render_template('add_person.html', name=name, gift_lst='\n'.join(sorted_gifts_lst))

        # Create a dictionary representing the new person
        new_person = {'name': name, 'gift_lst': sorted_gifts_lst}

        # Add the new person to the database
        person_id = g.storage.add_person(new_person, g.user_id)
        # Display a success message and redirect to the page for the newly added person
        flash(f"{new_person['name']} has been created.", "success")
        return redirect(url_for('person', id=person_id))

    # Render the form for adding a new person (GET request)
    return render_template('add_person.html')

# Route for editing an existing person's details
@app.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_person(id):
    # Redirect to login if the user is not logged in
    if not g.user_id:
        return redirect(url_for('login'))

    # Retrieve the person's data along with their gifts
    person = g.storage.find_person_with_gifts(id, g.user_id, page=1, gifts_per_page=100)  # Adjust gifts_per_page as needed

    # If the person is not found, display an error and redirect to the homepage
    if not person:
        flash("Person not found.", "error")
        return redirect(url_for('home'))

    # Handle the form submission when editing a person
    if request.method == "POST":
        # Get the updated name and gift list from the form
        new_name = request.form['name'].strip()
        gift_lst = parse_gift_list(request.form["gift_lst"].strip())

        # Validate the updated person data
        error = g.storage.validate_person(new_name, gift_lst, g.user_id, exclude_id=id)
        # If there's a validation error, display it and re-render the edit form
        if error:
            flash(error, "error")
            formatted_gift_lst = '\n'.join(person['gift_lst'])
            return render_template(
                'edit_person.html', id=id, name=person['name'], gift_lst=formatted_gift_lst
            )

        # Update the person's information in the database
        g.storage.update_person(person, new_name, gift_lst, g.user_id)
        # Display a success message and redirect to the person's details page
        flash(f"{new_name} has been modified.", "success")
        return redirect(url_for('person', id=id))

    # Render the form for editing an existing person (GET request)
    formatted_gift_lst = '\n'.join(person['gift_lst'])
    return render_template('edit_person.html', id=id, name=person['name'], gift_lst=formatted_gift_lst)

# Route for deleting a person
@app.route("/<int:id>/delete", methods=["POST"])
def delete_person(id):
    # Redirect to login if the user is not logged in
    if not g.user_id:
        return redirect(url_for('login'))
    # Find the person to be deleted to display a confirmation message
    person = g.storage.find_person(id, g.user_id)
    # Delete the person from the database
    g.storage.delete_person(id, g.user_id)
    # Display a success message and redirect to the homepage
    flash(f"{person['name']} has been deleted.", "success")
    return redirect(url_for('home'))

# Route for searching people and gifts, with pagination
@app.route("/search", defaults={'page': 1})
@app.route("/search/page/<int:page>")
def search(page):
    # Redirect to login if the user is not logged in
    if not g.user_id:
        return redirect(url_for('login'))

    # Get the search query from the request arguments
    query = request.args.get('query', '')
    gifts_per_page = GIFTS_PER_PAGE

    # Fetch all matching results (people and their gifts) based on the query
    results_data = g.storage.search_matching_with_gifts(
        query_str=query,
        user_id=g.user_id,
    )

    # Extract the list of results
    results = results_data.get('results', [])
    # Calculate the total number of gifts across all search results
    total_gifts = sum(len(result['paginated_gifts']) for result in results)
    # Calculate the total number of pages needed for pagination
    total_pages = math.ceil(total_gifts / gifts_per_page)

    # Redirect to the first page if the requested page is out of bounds
    if page < 1 or (total_pages > 0 and page > total_pages):
        return redirect(url_for('search', page=1, query=query))

    # Paginate the search results (gifts)
    start_index = (page - 1) * gifts_per_page
    end_index = start_index + gifts_per_page
    paginated_results = []
    current_count = 0

    # Iterate through the search results and extract the paginated gifts
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

    # Render the search results template
    return render_template(
        'search.html',
        query=query,
        results=paginated_results,
        page=page,
        total_pages=total_pages
    )

# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    # Handle the form submission for registration
    if request.method == "POST":
        # Get the username, password, and confirmation password from the form
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Perform basic input validation
        if not username:
            flash("Username is required.", "error")
            return render_template('register.html', username=username)
        if not password:
            flash("Password is required.", "error")
            return render_template('register.html', username=username)
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('register.html', username=username)

        # Check if a user with the given username already exists
        existing_user = g.storage.get_user_by_username(username)
        if existing_user:
            flash("Username already taken. Please choose another.", "error")
            return render_template('register.html', username=username)

        # Create a new user in the database
        user_id = g.storage.create_user(username, password)
        # If registration is successful, log the user in and redirect to the homepage
        if user_id:
            session['user_id'] = user_id
            flash("Registration successful! You are now logged in.", "success")
            return redirect(url_for('home'))
        # If registration fails, display an error message
        else:
            flash("Registration failed. Please try again.", "error")
            return render_template('register.html', username=username)
    # Render the registration form (GET request)
    return render_template('register.html')

# Route for user login
@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect to the homepage if the user is already logged in
    if g.user_id:
        return redirect(url_for('home'))
    # Handle the form submission for login
    if request.method == "POST":
        # Get the username and password from the form
        username = request.form['username'].strip()
        password = request.form['password']

        # Perform basic input validation
        if not username:
            flash("Username is required.", "error")
            return render_template('login.html')
        if not password:
            flash("Password is required.", "error")
            return render_template('login.html')

        # Retrieve the user from the database by username
        user = g.storage.get_user_by_username(username)
        # Check if the user exists and the password is correct
        if user and check_password_hash(user['password_hash'], password):
            # Store the user ID in the session to log the user in
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        # If login fails, display an error message
        else:
            flash("Invalid username or password.", "error")
            return render_template('login.html')
    # Render the login form (GET request)
    return render_template('login.html')

# Route for user logout
@app.route("/logout")
def logout():
    # Remove the user ID from the session to log the user out
    session.pop('user_id', None)
    # Display a logout message
    flash("You have been logged out.", "info")
    # Redirect to the homepage
    return redirect(url_for('home'))

# Error handler for 404 Not Found errors
@app.errorhandler(404)
def page_not_found(error):
    # Redirect to the homepage for unknown pages
    return redirect(url_for('home'))

# Run the Flask application if this script is executed directly
if __name__ == "__main__":
    # Determine the environment (production or development)
    if os.environ.get('FLASK_ENV') == 'production':
        # Run in production mode (no debugging)
        app.run(debug=False)
    else:
        # Run in development mode with debugging enabled on port 5003
        app.run(debug=True, port=5003)