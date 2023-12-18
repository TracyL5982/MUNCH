from html import escape  # Used to thwart XSS attacks.
from flask import Flask, request, make_response, redirect, url_for, jsonify, abort, render_template, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user, AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_mail import Mail, Message
from sqlite3 import connect as sqlite_connect
from sqlalchemy import create_engine
from sys import argv, stderr, exit
import os
import re
import model.classroom as classroom
import model.user as user
from model.database import User, Match, Base
import model.email as email

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

#-----------------------------------------------------------------------
# Flask-Mail setup
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'munchyale@gmail.com'
app.config['MAIL_PASSWORD'] = 'deacdbbxdtyylfde'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

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
        return render_template('login.html')

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

    user_ids = classroom.get_all_users(classroom_id)
    users_info = []
    for user_id in user_ids:
        user_info = user.get_user_info(user_id)
        print(user_info)
        user_info['score'] = classroom.get_user_classroom_score(classroom_id, user_id)
        users_info.append(user_info)

    admin_ids = classroom.get_admins(classroom_id)
    print(f"admins: {admin_ids}")
    admins_info = []
    for admin_id in admin_ids:
        admins_info.append(user.get_user_info(admin_id))

    is_member = current_user.user_id in user_ids
    is_admin = classroom.check_admin(classroom_id, current_user.user_id)

    is_3pair = False

    if is_member:
        match = classroom.get_user_match(classroom_id, current_user.user_id)
        if match:
            if len(match) > 1:
                is_3pair = True
    else:
        match = None
    print(match)

    html = render_template("classrooms.html",
                           is_admin = is_admin,
                           is_member=is_member,
                           match = match,
                           is_3pair=is_3pair,
                           users = users_info,
                           admins = admins_info,
                           classroom_info = classroom_info,
                           classroom_id = classroom_id)
    response = make_response(html)
    return response

@app.route('/join-classroom', methods=['GET'])
@login_required
def join_classroom():
    """
    join a classroom
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")
    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")
    
    #Check if the classroom exists
    if not classroom.classroom_exists(classroom_id):
        flash("This classroom does not exist.")
        return redirect(url_for('index'))

    user_id = request.args.get('user_id')
    if not user_id:
        print("no user id provided")
    else:
        try:
            user_id = int(user_id)
        except ValueError:
            abort(400, "user_id is not an integer")

        classroom.add_user(classroom_id, user_id)

    return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

#######################################################################
@app.route('/classrooms/create', methods=['POST'])
@login_required
def create_classroom():
    """
    create a new classroom
    """
    print("make new classroom")
    admin_usernames = request.form.get('admin_usernames').split(',')
    if not admin_usernames:
        flash("Need to provide at least one valid admin per classroom")
        return redirect(url_for('index'))

    admin_ids = []
    for username in admin_usernames:
        usr = user.get_user_by_name(username.strip())
        if not usr:
            flash(f"User {username.strip()} not found.")
        else:
            user_id = usr.user_id
            admin_ids.append(user_id)

    if not admin_ids:
        flash("Need to provide at least one valid admin per classroom")
        return redirect(url_for('index'))

    try:
        admin_ids = [int(admin_id) for admin_id in admin_ids]
    except ValueError:
        flash("admin_id is not an integer")
        return redirect(url_for('index'))

    classroom_name = request.form.get('classroom_name')
    if not classroom_name:
        flash("Need to provide a classroom name")
        return redirect(url_for('index'))
    classroom_bio = request.form.get('classroom_bio')
    if not classroom_bio:
        flash("Need to provide a classroom bio")
        return redirect(url_for('index'))

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

    classroom_name = request.args.get('classroom_name')
    if not classroom_name:
        abort(400, "Classroom name not provided")

    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
    else:
        html = render_template("classroom_settings.html",
                            classroom_id = classroom_id,
                            classroom_name = classroom_name)
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
    add admins to classroom by name
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
        return make_response(html)
    
    admin_names = request.form.get('admin_names').split(',')
    if not admin_names:
        abort(400, "No usernames provided")
    admin_ids = []
    for username in admin_names:
        usr = user.get_user_by_name(username.strip())
        if not usr:
            flash(f"User {username.strip()} not found.")
        else:
            user_id = usr.user_id
            admin_ids.append(user_id)

    if not admin_ids:
        flash("Need to provide at least one valid user")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

    try:
        admin_ids = [int(admin_id) for admin_id in admin_ids]
    except ValueError:
        flash("Admin id is not an integer")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

    result = classroom.add_admins(classroom_id, admin_ids, current_user.user_id)
    if result:
        flash(f"Admins {result['new_admins']} successfully added!")
    else:
        flash("Error adding admins")
    return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

@app.route('/classrooms/remove_admin', methods=['POST'])
@login_required
def delete_admin():
    """
    remove an admin from classroom - but can't remove ALL of them
    each classroom must always have ONE admin
    remove by giving NAME of the admin
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
        return make_response(html)

    admin_name = request.form.get('admin_name')
    if not admin_name:
        abort(400, "No admin to delete provided")
    admin = user.get_user_by_name(admin_name)
    if not admin:
        flash("Admin not found")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

    removal_result = classroom.delete_admin(classroom_id, admin.user_id, current_user.user_id)
    if removal_result:
        flash("Admin removed successfully.")
    else:
        flash("Failed to remove admin. They either do not administrate this classroom or are the sole admin.")
    return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

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

    if not classroom.classroom_exists(classroom_id):
        flash("This classroom does not exist.")
        return redirect(url_for('index'))

    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
        return make_response(html)
    
    matches = classroom.get_current_match(classroom_id, current_user.user_id)
    odd_group_exists = False
    if matches:
        odd_group_exists = any('user3_id' in match for match in matches)
    html = render_template("matchpage.html", matches=matches, classroom_id=classroom_id, odd_group_exists=odd_group_exists)
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

    if not classroom.classroom_exists(classroom_id):
        flash("This classroom does not exist.")
        return redirect(url_for('index'))

    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
        return make_response(html)
    
    odd_group_exists = False
    cls_name = classroom.get_info(classroom_id)["classroom_name"]

    # first need to check that there are at least 2 users
    if len(classroom.get_all_users(classroom_id)) < 2:
        matches = None
    else:
        matches = classroom.make_new_match(classroom_id, current_user.user_id)
        print(matches)
        odd_group_exists = any('user3_id' in match for match in matches)

    for match in matches:
        email.send_match_notification(mail, match, cls_name)
    html = render_template("matchpage.html", matches=matches, classroom_id=classroom_id, odd_group_exists=odd_group_exists)
    response = make_response(html)
    return response

@app.route('/classrooms/admin/notify', methods=['POST'])
@login_required
def daily_notification():
    """
    send notification
    """
    classroom_id = request.args.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")
    
    classroom_users = classroom.get_all_users(classroom_id)
    cls_name = classroom.get_info(classroom_id)["classroom_name"]

    emails = []
    for user_id in classroom_users:
        user_email = user.get_user_info(user_id)
        emails.append(user_email["user_email"])
    
    email.send_daily_reminder(mail, emails, cls_name)
    return jsonify(True)

@app.route('/classrooms/admin/completematch', methods=['POST'])
@login_required
def mark_match_complete():
    """
    marks a match complete and increments each involved user's
    score by 1 
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")
    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")

    if not classroom.classroom_exists(classroom_id):
        flash("This classroom does not exist.")
        return redirect(url_for('index'))

    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
        return make_response(html)
    
    user1_id = request.form.get('user1')
    if not user1_id:
        abort(400, "user id not provided")
    try:
        user1_id = int(user1_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    user2_id = request.form.get('user2')
    if not user2_id:
        abort(400, "user id not provided")
    try:
        user2_id = int(user2_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    user3_id = request.form.get('user3')
    if not user3_id:
        user3_id = None
    else:
        try:
            user3_id = int(user3_id)
        except ValueError:
            abort(400, "user_id is not an integer")

    match_id = request.form.get('match_id')
    if not match_id:
        match_id = None
    else:
        try:
            match_id = int(match_id)
        except ValueError:
            abort(400, "match_id is not an integer")

    return jsonify(classroom.mark_match_complete(classroom_id, current_user.user_id, match_id=match_id, user1_id=user1_id, user2_id=user2_id, user3_id=user3_id))

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
    
    if not classroom.classroom_exists(classroom_id):
        flash("This classroom does not exist.")
        return redirect(url_for('index'))

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
    """
    add users to classroom by name
    """
    classroom_id = request.form.get('classroom_id')
    if not classroom_id:
        abort(400, "Classroom id not provided")

    try:
        classroom_id = int(classroom_id)
    except ValueError:
        abort(400, "classroom_id is not an integer")
    
    if not classroom.classroom_exists(classroom_id):
        flash("This classroom does not exist.")
        return redirect(url_for('index'))

    user_names = request.form.get('user_names').split(',')
    if not user_names:
        abort(400, "No usernames provided")
    user_ids = []
    for username in user_names:
        usr = user.get_user_by_name(username.strip())
        if not usr:
            flash(f"User {username.strip()} not found.")
        else:
            user_id = usr.user_id
            user_ids.append(user_id)

    if not user_ids:
        flash("Need to provide at least one valid user per classroom")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

    try:
        user_ids = [int(user_id) for user_id in user_ids]
    except ValueError:
        flash("user_id is not an integer")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

    result = classroom.add_users(classroom_id, user_ids, current_user.user_id)
    if result:
        flash(f"Users {result['user_ids']} successfully added!")
    else:
        flash("Error adding users")
    return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

@app.route('/classrooms/reset_score', methods=['POST'])
@login_required
def reset_student_score():
    """
    reset's user classroom-specific score to 0
    """
    classroom_id = request.form.get('classroom_id')

    student_name = request.form.get('student_name')
    if not student_name:
        abort(400, "user not provided")

    student = user.get_user_by_name(student_name)
    if not student:
        flash("Student not found.")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))
        
    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
        return make_response(html)
    
    reset_result = classroom.reset_user_classroom_score(classroom_id, student.user_id, current_user.user_id)
    if reset_result:
        flash("Student score reset successfully.")
    else:
        flash("Failed to reset student's score. They may not be in this classroom.")

    return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

@app.route('/classrooms/remove_student', methods=['POST'])
@login_required
def remove_student():
    """
    remove user from classroom
    """
    classroom_id = request.form.get('classroom_id')

    student_name = request.form.get('student_name')
    if not student_name:
        abort(400, "user not provided")

    student = user.get_user_by_name(student_name)
    if not student:
        flash("Student not found.")
        return redirect(url_for('get_classroom_info', classroom_id=classroom_id))
        
    if not classroom.check_admin(classroom_id, current_user.user_id):
        html = render_template("error.html",
                               error_message = "Access denied: Admin status required beyond this point.")
        return make_response(html)
    
    removal_result = classroom.remove_user(classroom_id, student.user_id, current_user.user_id)
    if removal_result:
        flash("Student removed successfully.")
    else:
        flash("Failed to remove student. They may not be in this classroom.")

    return redirect(url_for('get_classroom_info', classroom_id=classroom_id))

@app.route('/classrooms/leave', methods=['POST'])
@login_required
def leave_classroom():
    classroom_id = request.form['classroom_id']

    # Remove the current user from the classroom
    removal_result = classroom.remove_user(classroom_id, current_user.user_id, current_user.user_id)
    if removal_result:
        flash("You have left the classroom.")
    else:
        flash("Error leaving classroom.")

    return redirect(url_for('index'))  

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
        class_ids = user_dict['classrooms']
        class_names = ""
        for cls in class_ids:
            cls_id = cls[0]
            cls_name = classroom.get_info(cls_id)["classroom_name"]
            cls_score = classroom.get_user_classroom_score(cls_id, user_id)
            class_names += f"{cls_name} (score: {cls_score}), "
        if len(class_names) > 0:
            class_names = class_names[:-2]

        admin_ids = user_dict['admin_classrooms']
        admin_names = ""
        for cls in admin_ids:
            cls_id = cls[0]
            cls_name = classroom.get_info(cls_id)["classroom_name"]
            admin_names += cls_name + ", "
        if len(admin_names) > 0:
            admin_names = admin_names[:-2]

        html = render_template('profile.html',
            name=user_dict['user_name'],
            email=user_dict['user_email'],
            phone=user_dict['user_phone'],
            classrooms=class_names,
            admin_classrooms=admin_names)
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
        class_ids = user_dict['classrooms']
        class_names = ""
        for cls in class_ids:
            cls_id = cls[0]
            cls_name = classroom.get_info(cls_id)["classroom_name"]
            cls_score = classroom.get_user_classroom_score(cls_id, current_user.user_id)
            class_names += f"{cls_name} (score: {cls_score}), "
        if len(class_names) > 0:
            class_names = class_names[:-2]

        admin_ids = user_dict['admin_classrooms']
        admin_names = ""
        for cls in admin_ids:
            cls_id = cls[0]
            cls_name = classroom.get_info(cls_id)["classroom_name"]
            admin_names += cls_name + ", "
        if len(admin_names) > 0:
            admin_names = admin_names[:-2]

        html = render_template('profile.html',
            user_id=user_dict['user_id'],
            name=user_dict['user_name'],
            email=user_dict['user_email'],
            phone=user_dict['user_phone'],
            classrooms=class_names,
            admin_classrooms=admin_names)
    else:
        html = render_template('profile.html', name=None)
    response = make_response(html)
    return response

@app.route('/update_username', methods=['POST'])
@login_required
def update_user_name():
    """
    update user
    """
    current_user_id = current_user.get_id()
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    if current_user_id != user_id:
        abort(403, "Unauthorized access")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    new_name = request.form.get('name')
    if new_name:
        user.update_user_name(user_id, new_name)

    return redirect(url_for ('get_profile_info'))

@app.route('/update_email', methods=['POST'])
@login_required
def update_user_email():
    """
    update user
    """
    current_user_id = current_user.get_id()
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    if current_user_id != user_id:
        abort(403, "Unauthorized access")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    new_email = request.form.get('email')
    if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            flash("Invalid email address.")
            return redirect(url_for('get_profile_info'))
    if new_email:
        user.update_user_email(user_id, new_email)
    return redirect(url_for('get_profile_info'))

@app.route('/update_phone', methods=['POST'])
@login_required
def update_user_phone():
    """
    update user
    """
    current_user_id = current_user.get_id()
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400, "user not provided")
    if current_user_id != user_id:
        abort(403, "Unauthorized access")
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, "user_id is not an integer")

    new_phone = request.form.get('phone')
    if not re.match(r"\d", new_phone):
        flash("Invalid phone number.")
        return redirect(url_for('get_profile_info'))
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

# -----------------------------------------------------------------------

@app.route('/about', methods=['GET'])
@login_required
def about():
    html = render_template("about.html")
    response = make_response(html)
    return response

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
