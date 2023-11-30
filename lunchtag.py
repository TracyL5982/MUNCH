from html import escape  # Used to thwart XSS attacks.
from flask import Flask, request, make_response, redirect, url_for, jsonify, abort, render_template, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user, AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlite3 import connect as sqlite_connect
from sqlalchemy import create_engine
from sys import argv, stderr, exit
import os
import re
import model.classroom as classroom
import model.user as user
from model.database import User,Base

"""the controller for our flask app"""
#-----------------------------------------------------------------------
DATABASE_NAME = 'model/lunchtag.sqlite'
app = Flask(__name__, template_folder='view')
app.secret_key = os.urandom(24)

#-----------------------------------------------------------------------
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
engine = create_engine('sqlite://',
                       creator=lambda: sqlite_connect(
                           'file:' + DATABASE_NAME + '?mode=rw', uri=True))
Session = scoped_session(sessionmaker(bind=engine))

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    try:
        user = session.query(User).get(int(user_id))
        if not user:
            return None
        else:
            return user
    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()
#-----------------------------------------------------------------------

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@login_required
def index():
    classrooms = classroom.get_all_classrooms()
    res = []
    for cls in classrooms:
        res.append([cls.classroom_id, cls.classroom_name, cls.classroom_bio])
    # user = load_user()
    html = render_template("index.html",
                           classrooms = res)
    response = make_response(html)
    return response

#-----------------------------------------------------------------------

# LOGIN ENDPOINTS
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['email']
    # Fetch the user by email
    user_obj = user.get_user_by_email(email)

    # Check if user exists and the password is correct
    if user_obj and user_obj.check_password(request.form['password']):
        # The user should be logged in now
        login_user(user_obj)
        return redirect(url_for('index'))
    else:
        # If the login credentials are incorrect
        flash('Invalid email or password')
        return abort(401, "Incorrect username or password")

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        ## INPUT CHEKCING ##
        # Check for unique username
        if user.get_user_by_name(name):
            flash("Username already taken.")
            return render_template('register.html')

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address.")
            return render_template('register.html')

        # Basic phone number validation
        if not re.match(r"\d", phone):
            flash("Invalid phone number.")
            return render_template('register.html')

        # Check if password and confirm password match
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template('register.html')

        if user.create_user(name, email, phone, password):
            return redirect(url_for('login'))
        else:
            flash("Error creating user.")
            return render_template('register.html')

    return render_template('register.html')

#-----------------------------------------------------------------------

# CLASSROOM ENDPOINTS

@app.route('/classrooms', methods=['GET'])
@login_required
def get_classroom_info():
    """
    returns a list of all user information for
    a given classroom id, and loads the classrooms
    page which displays the classroom info.
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    classroom_info = classroom.get_info(classroom_id)

    print("HERE")
    user_id = request.args.get('user_id')
    print("user id is", user_id)
    if not user_id:
        print("no user id provided")
    else:
        try:
            user_id = int(user_id)
        except ValueError:
            abort(400, "user_id is not an integer")

        print("adding user", [user_id], "to classroom", classroom_id) #TODO: check that this works
        classroom.add_user(classroom_id, user_id)

    user_ids = classroom.get_all_users(classroom_id)
    users_info = []
    for user_id in user_ids:
        users_info.append(user.get_user_info(user_id))

    admin_ids = classroom.get_admins(classroom_id)
    print(f"admins: {admin_ids}")
    admins_info = []
    for admin_id in admin_ids:
        admins_info.append(user.get_user_info(admin_id))

    is_admin = classroom.check_admin(classroom_id, current_user.user_id)
    if not is_admin:
        match = classroom.get_user_match(classroom_id, current_user.user_id)
    else:
        match = None
    print(match)

    html = render_template("classrooms.html",
                           is_admin = is_admin,
                           match = match,
                           users = users_info,
                           admins = admins_info,
                           classroom_info = classroom_info,
                           classroom_id = classroom_id)
    response = make_response(html)
    return response

#######################################################################
@app.route('/classrooms/create', methods=['POST'])
@login_required
def create_classroom():
    """
    create a new classroom
    """
    print("make new classroom")
    admin_ids = request.form.get('admin_ids').split(',') # can start with multiple ?
    if not admin_ids:
        abort(400, "Need to provide at least one admin per classroom")

    classroom_name = request.form.get('classroom_name')
    if not classroom_name:
        abort(400, "Need to provide a classroom name")
    classroom_bio = request.form.get('classroom_bio')
    if not classroom_bio:
        abort(400, "Need to provide a classroom bio")

    try:
        admin_ids = [int(admin_id) for admin_id in admin_ids]
    except ValueError:
        abort(400, "admin_id is not an integer")

    result = classroom.create_classroom(admin_ids, classroom_name, classroom_bio)
    if result:
        flash("Classroom successfully created!")
        return redirect(url_for('index'))
    else:
        flash("Error creating classroom")
        return redirect(url_for('index'))

@app.route('/classrooms/settings', methods=['GET'])
@login_required
def get_classroom_settings():
    """
    loads the classroom settings page,
    which allows changing name, bio, and
    adding admins or users.
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
    else:
        html = render_template("classroom_settings.html",
                            classroom_id = classroom_id)
    response = make_response(html)
    return response

@app.route('/classrooms/update/name', methods=['PUT'])
@login_required
def update_classroom_name():
    classroom_id = request.form.get('classroom_id')
    classroom_name = request.form.get('classroom_name')

    try:
        classroom_id = int(classroom_id)
        result = classroom.update_classroom_name(classroom_id, classroom_name, current_user.user_id)
        if result:
            flash("Classroom name updated successfully", "success")
        else:
            flash("Failed to update classroom name", "error")
    except ValueError:
        flash("Invalid classroom ID", "error")
    except Exception as e:
        flash(str(e), "error")
    return jsonify({"success": True, "message": "Classroom name updated successfully"})

@app.route('/classrooms/update/bio', methods=['PUT'])
@login_required
def update_classroom_bio():
    classroom_id = request.form.get('classroom_id')
    classroom_bio = request.form.get('classroom_bio')

    try:
        classroom_id = int(classroom_id)
        result = classroom.update_classroom_bio(classroom_id, classroom_bio, current_user.user_id)
        if result:
            flash("Classroom bio updated successfully", "success")
        else:
            flash("Failed to update classroom bio", "error")
    except ValueError:
        flash("Invalid classroom ID", "error")
    except Exception as e:
        flash(str(e), "error")
    return jsonify({"success": True, "message": "Classroom bio updated successfully"})

@app.route('/classrooms/delete', methods=['DELETE'])
@login_required
def delete_classroom():
    classroom_id = request.form.get('classroom_id')
    try:
        classroom_id = int(classroom_id)
        result = classroom.delete_classroom(classroom_id, current_user.user_id)
        if result:
            flash("Classroom deleted successfully", "success")
        else:
            flash("Failed to delete classroom", "error")
    except ValueError:
        flash("Invalid classroom ID", "error")
    except Exception as e:
        flash(str(e), "error")
    return jsonify({"success": True, "message": "Classroom deleted successfully"})

#-----------------------------------------------------------------------
# ADMINS

@app.route('/classrooms/admin', methods=['GET'])
@login_required
def get_admins():
    """
    get the list of admins for a classroom
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    return jsonify(classroom.get_admins(classroom_id))

@app.route('/classrooms/admin', methods=['POST'])
@login_required
def add_admins():
    """
    add admins to classroom
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    admin_ids = request.form.get('admin_ids')
    if not admin_ids:
        abort(400, "No new admin(s) provided")

    return jsonify(classroom.add_admins(classroom_id, admin_ids, current_user.user_id))


# TODO: change endpoint url
@app.route('/classrooms/admin', methods=['DELETE'])
@login_required
def delete_admins():
    """
    remove admins from classroom - but can't remove ALL of them
    each classroom must always have ONE admin
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    admin_ids = request.form.get('admin_ids')
    if not admin_ids:
        abort(400, "No admin(s) to delete provided")

    return jsonify(classroom.delete_admins(classroom_id, admin_ids, current_user.user_id))

# MATCH

@app.route('/classrooms/admin/match', methods=['GET'])
@login_required
def get_current_match():
    """
    returns the list of current pairings (from the last match)
    OR if one doesn't already exist, returns a new list of pairings
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    matches = classroom.get_current_match(classroom_id, current_user.user_id)
    html = render_template("matchpage.html", matches=matches)
    response = make_response(html)
    return response


@app.route('/classrooms/admin/match', methods=['POST'])
@login_required
def make_new_match():
    """
    generates new lunch tag pairings
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    # first need to check that there are at least 2 users
    if len(classroom.get_all_users(classroom_id)) < 2:
        matches = None
    else:
        matches = classroom.make_new_match(classroom_id, current_user.user_id)
        print(matches)
    html = render_template("matchpage.html", matches=matches)
    response = make_response(html)
    return response

# USERS
@app.route('/classrooms/users', methods=['GET'])
@login_required
def get_users():
    """
    if given a user id, will check whether the specific user is in the classroom
    otherwise, returns a list of all the users in the classroom
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    user_id = request.args.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            abort(400, "user_id is not an integer")
        return jsonify(classroom.check_user(classroom_id, user_id))
    else:
        return jsonify(classroom.get_all_users(classroom_id))

@app.route('/classrooms/users', methods=['POST'])
@login_required
def add_users():
    # TODO: decide whether this should be an admin only action - in that case, change endpoint
    """
    add user to classroom
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    user_ids = request.form.get('user_ids').split(',')
    if not user_ids:
        abort(400, "Need to provide at least one user per classroom")

    try:
        user_ids = [int(user_id) for user_id in user_ids]
    except ValueError:
        abort(400, "user_id is not an integer")

    result = classroom.add_users(classroom_id, user_ids, current_user.user_id)
    if result:
        flash(f"Users {result['user_ids']} successfully added!")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))
    else:
        flash("Error adding users")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

@app.route('/classrooms/users', methods=['DELETE'])
@login_required
def remove_user():
    """
    remove user from classroom
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    return jsonify(classroom.remove_user(classroom_id, user_id, current_user.user_id))


#-----------------------------------------------------------------------

# USERS ENDPOINTS

@app.route('/users', methods=['GET'])
@login_required
def get_user_info():
    """
    get user information
    """
    user_id = request.args.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    user_dict = user.get_user_info(user_id)
    if user_dict:
        html = render_template('profile.html',
            name=user_dict['user_name'],
            email=user_dict['user_email'],
            phone=user_dict['user_phone'],
            score=user_dict['score'],
            classrooms=user_dict['classrooms'],
            admin_classrooms=user_dict['admin_classrooms'])
    else:
        html = render_template('profile.html', name=None)
    response = make_response(html)
    return response

@app.route('/users/profile', methods=['GET'])
@login_required
def get_profile_info():
    """
    get current user information for profile page
    """
    user_dict = user.get_user_info(current_user.user_id)
    if user_dict:
        html = render_template('profile.html',
            user_id=user_dict['user_id'],
            name=user_dict['user_name'],
            email=user_dict['user_email'],
            phone=user_dict['user_phone'],
            score=user_dict['score'],
            classrooms=user_dict['classrooms'],
            admin_classrooms=user_dict['admin_classrooms'])
    else:
        html = render_template('profile.html', name=None)
    response = make_response(html)
    return response


@app.route('/users', methods=['POST'])
@login_required
def create_user():
    """
    create user
    """
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    # TODO: input validation

    return jsonify(user.create_user(name, email, phone))


@app.route('/update_username', methods=['POST'])
@login_required
def update_user_name():
    """
    update user
    """
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    new_name = request.form.get('name')
    if new_name:
        # TODO: input validation
        user.update_user_name(user_id, new_name)

    return redirect(url_for ('get_profile_info'))

@app.route('/update_email', methods=['POST'])
@login_required
def update_user_email():
    """
    update user
    """
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    new_email = request.form.get('email')
    # TODO: input validation
    if new_email:
        user.update_user_email(user_id, new_email)
    return redirect(url_for('get_profile_info'))

@app.route('/update_phone', methods=['POST'])
@login_required
def update_user_phone():
    """
    update user
    """
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    new_phone = request.form.get('phone')
    # TODO: input validation
    if new_phone:
        user.update_user_phone(user_id, new_phone)
    return redirect(url_for('get_profile_info'))

@app.route('/users', methods=['DELETE'])
@login_required
def delete_user():
    """
    delete user
    """
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    return jsonify(user.delete_user(user_id))


#-----------------------------------------------------------------------

# FEED ENDPOINTS

@app.route('/feed', methods=['GET'])
@login_required
def get_feed():
    """
    returns a list of all classrooms for the given user
    """
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    return NotImplemented
    # return jsonify(feed.get_classrooms(user_id))


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
