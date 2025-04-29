import secrets
import os
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from helpers.utils import parse_gift_list, sort_gifts, sort_names
from helpers.database_persistence import DatabasePersistence

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

@app.before_request
def load_db():
    g.storage = DatabasePersistence()

@app.route("/")
def home():
    people_gift_list = g.storage.get_all_people()
    sorted_people = sort_names(people_gift_list)
    return render_template('home.html', people=sorted_people)

@app.route("/<int:id>")
def person(id):
    person = g.storage.find_person(id)
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
    if request.method == "POST":
        name = request.form["name"].strip()
        gift_lst = parse_gift_list(request.form["gifts"].strip())
        sorted_gifts_lst = sort_gifts(gift_lst)

        error = g.storage.validate_person(name, sorted_gifts_lst)
        if error:
            flash(error, "error")
            return render_template('add_person.html', name=name, gift_lst='\n'.join(sorted_gifts_lst))

        new_person = {'name': name, 'gift_lst': sorted_gifts_lst}

        person_id = g.storage.add_person(new_person)
        flash(f"{new_person['name']} has been created.", "success")
        return redirect(url_for('person', id=person_id))

    return render_template('add_person.html')

@app.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_person(id):
    person = g.storage.find_person(id)

    if not person:
        flash("Person not found.", "error")
        return redirect(url_for('home'))

    if request.method == "POST":
        new_name = request.form['name'].strip()
        gift_lst = parse_gift_list(request.form["gift_lst"].strip())

        error = g.storage.validate_person(new_name, gift_lst, exclude_id=id)
        if error:
            flash(error, "error")
            formatted_gift_lst = '\n'.join(person['gift_lst'])
            return render_template(
                'edit_person.html', id=id, name=person['name'], gift_lst=formatted_gift_lst
            )

        g.storage.update_person(person, new_name, gift_lst)
        flash(f"{new_name} has been modified.", "success")
        return redirect(url_for('person', id=id))

    formatted_gift_lst = '\n'.join(person['gift_lst'])
    return render_template('edit_person.html', id=id, name=person['name'], gift_lst=formatted_gift_lst)

@app.route("/<int:id>/delete", methods=["POST"])
def delete_person(id):
    person = g.storage.find_person(id)
    g.storage.delete_person(id)
    flash(f"{person['name']} has been deleted.", "success")
    return redirect(url_for('home'))

@app.route("/search")
def search():
    query = request.args.get('query', '')
    results = g.storage.search_matching(query)
    return render_template('search.html', query=query, results=results)

@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('home'))

if __name__ == "__main__":
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)
