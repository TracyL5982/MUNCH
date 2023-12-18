from sys import argv, stderr, exit
from sqlite3 import connect as sqlite_connect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import random

from model.database import Classroom, User, Match, user_classroom_association, DATABASE_NAME

"""
classroom module for functions relating to classroom object
"""

"""
This module provides a set of functions to manipulate and manage classroom entities within a database.
It includes capabilities to create, retrieve, update, and delete classrooms, manage classroom admins,
and handle user matching within classrooms.

Functions:

****CLASSROOM****
    get_all_classrooms():
        return classrooms
    get_info(classroom_id):
        return {"classroom_name": classroom.classroom_name,
                "classroom_bio": classroom.classroom_bio}
    create_classroom(admin_ids, classroom_name, classroom_bio):
        return {"classroom_id": new_classroom.classroom_id,
                "classroom_name": new_classroom.classroom_name,
                "classroom_bio": new_classroom.classroom_bio}
    update_classroom_name(classroom_id, classroom_name, curr_user):
        return {
                "classroom_id": classroom.classroom_id,
                "classroom_name": classroom.classroom_name
            }
    update_classroom_bio(classroom_id, classroom_bio, curr_user):
        return {"classroom_id": classroom.classroom_id,
                "classroom_name": classroom.classroom_name,
                "classroom_bio": classroom.classroom_bio}
    delete_classroom(classroom_id, curr_user):
        return classroom_id

****ADMIN****
    check_admin(classroom_id, user_id):
        return True/False
    get_admins(classroom_id):
        return admin_ids
    add_admins(classroom_id, admin_ids, curr_user):
        return {"classroom_id": classroom.classroom_id,
                "classroom_admins": classroom.admins}
    delete_admins(classroom_id, admin_ids, curr_user):
        return {"classroom_id": classroom.classroom_id,
                "classroom_admins": classroom.admins}

****MATCH****
    get_user_match(classroom_id, user_id):
        return user_id
    get_current_match(classroom_id, curr_user):
        return matches
    make_new_match(classroom_id, curr_user):
        return new_match

****USER****
    check_user(classroom_id, user_id):
        return True/False
    get_all_users(classroom_id): Retrieve all users within a classroom.
        return user_ids
    add_user(classroom_id, user_id, curr_user): Add a user to a classroom.
        return {"classroom_id": classroom.classroom_id,
                "user_id": user_id}
    remove_user(classroom_id, user_id, curr_user): Remove a user from a classroom.
        return {"classroom_id": classroom.classroom_id,
                "user_id": user_id}
"""


engine = create_engine('sqlite://',
                       creator=lambda: sqlite_connect(
                           'file:' + DATABASE_NAME + '?mode=rw', uri=True))

def get_all_classrooms():
    """
    retrieves information on all classrooms
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classrooms = session.query(Classroom).all()

        session.close()
        engine.dispose()

        # print(classrooms)
        return classrooms
    except Exception as ex:
        print(ex, file=stderr)
        session.close()
        engine.dispose()
        exit(1)

def get_info(classroom_id):
    """
    retrieves information on one classroom,
    specified by the given classroom_id
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter_by(classroom_id=classroom_id).first()

        session.close()
        engine.dispose()

        if not classroom:
            return None
        else:
            return {"classroom_name": classroom.classroom_name,
                    "classroom_bio": classroom.classroom_bio}
    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def classroom_exists(classroom_id):
    """
    Check if a classroom with the given classroom_id exists in the database.
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter_by(classroom_id=classroom_id).first()

        session.close()
        engine.dispose()

        return classroom is not None
    except Exception as ex:
        print(ex, file=stderr)
        return False

def create_classroom(admin_ids, classroom_name, classroom_bio):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        #classroom name is required to create a classroom
        if(classroom_name is None or classroom_name.strip() == ""):
            print ("Need to enter a classroom name to create a new classroom")
            session.close()
            engine.dispose()
            return None

        new_classroom = Classroom(classroom_name=classroom_name, classroom_bio=classroom_bio)
        session.add(new_classroom)
        session.flush()  # Flush here to ensure 'new_classroom' gets an ID

        # Check if all admin_ids correspond to a real user
        real_admins = session.query(User.user_id).filter(User.user_id.in_(admin_ids)).all()
        real_admin_ids = [admin.user_id for admin in real_admins]
        if set(admin_ids) != set(real_admin_ids):
            missing_admins = set(admin_ids) - set(real_admin_ids)
            print(f"Error: The following admin IDs do not correspond to any real user: {missing_admins}")
            return None

        admins = session.query(User).filter(User.user_id.in_(admin_ids)).all()
        for admin in admins:
            new_classroom.admins.append(admin)
        session.commit()

        return {"classroom_id": new_classroom.classroom_id, "classroom_name": new_classroom.classroom_name, "classroom_bio": new_classroom.classroom_bio}

    except Exception as ex:
        print(ex, file=stderr)
        return None
    finally:
        session.close()

def update_classroom_name(classroom_id, classroom_name, curr_user):
    """
    updates the classroom name.
    admin only.
    """
    if not check_admin(classroom_id, curr_user):
        return None
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if classroom:
            classroom.classroom_name = classroom_name
            session.commit()
            return {
                "classroom_id": classroom.classroom_id,
                "classroom_name": classroom.classroom_name
            }
        else:
            print(f"No classroom found with ID {classroom_id}", file=stderr)
            return None
    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def update_classroom_bio(classroom_id, classroom_bio, curr_user):
    """
    updates classroom bio.
    admin only.
    """
    if not check_admin(classroom_id, curr_user):
        return None
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if classroom:
            classroom.classroom_bio = classroom_bio
            session.commit()
            print(f"Classroom {classroom_id} updated successfully.")
            ret = {"classroom_id": classroom.classroom_id,
                   "classroom_name": classroom.classroom_name,
                   "classroom_bio": classroom.classroom_bio}
        else:
            print(f"No classroom found with ID {classroom_id}")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def delete_classroom(classroom_id, curr_user):
    if not check_admin(classroom_id, curr_user):
        return None
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if classroom:
            session.delete(classroom)
            session.commit()
            print(f"Classroom {classroom_id} deleted successfully.")
        else:
            print(f"No classroom found with ID {classroom_id}")

        return classroom_id

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()


# ADMINS
def check_admin(classroom_id, user_id):
    """
    checks if user_id is an admin in classroom with classroom_id
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).filter(User.user_id == user_id).first()
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()

        if classroom and user and user in classroom.admins:
            print(f"User {user_id} is an admin for Classroom {classroom_id}.")
            return True
        else:
            print(f"User {user_id} is NOT an admin for Classroom {classroom_id}.")
            return False

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def get_admins(classroom_id):
    """
    gets the list of all admins of a given classroom
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()

        if classroom:
            admins = [admin.user_id for admin in classroom.admins]
            print(f"Admins for Classroom {classroom_id}: {admins}")
            return admins
        else:
            print(f"No classroom found with ID {classroom_id}")
            return None

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def add_admins(classroom_id, admin_ids, curr_user):
    if not check_admin(classroom_id, curr_user):
        return None
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if classroom:
            new_admins = []
            for admin_id in admin_ids:
                admin = session.query(User).filter(User.user_id == admin_id).first()
                if admin and admin not in classroom.admins:
                    classroom.admins.append(admin)
                    new_admins.append(admin.user_id)

            session.commit()
            print(f"Admins added to Classroom {classroom_id}.")
            ret = {"classroom_id": classroom.classroom_id, "classroom_admins": classroom.admins, "new_admins": new_admins}
        else:
            print(f"No classroom found with ID {classroom_id}")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        return None
    finally:
        session.close()

def delete_admin(classroom_id, admin_id, curr_user):
    """
    delete one admin from a classroom if they are not the only admin.
    """
    if not check_admin(classroom_id, curr_user):
        return None
    
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if classroom: 
            # should never be able to remove more admins than there are currently, always need 1
            if len(classroom.admins) == 1:
                return None

            admin = session.query(User).filter(User.user_id == admin_id).first()
            if admin in classroom.admins:
                classroom.admins.remove(admin)

            session.commit()
            print(f"Admin removed from Classroom {classroom_id}.")
            ret = {"classroom_id": classroom.classroom_id, "classroom_admins": classroom.admins, "removed_admin": admin_id}
        else:
            print(f"No classroom found with ID {classroom_id}")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        return None
    finally:
        session.close()

# MATCH
def get_user_match(classroom_id, user_id):
    """
    given a user_id, returns either the user(s) 
    they are currently matched to in a list of Users
    or None if there is no match yet
    """
    # check if there is currently a match
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # verify that classroom exists
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"No classroom found with ID {classroom_id}")
            return None

        print(len(classroom.matches))
        m = []
        for match in classroom.matches:
            print(match.user1_id)
            if match.user1.user_id == user_id:
                m.append(match.user2)
                if match.user3:
                    m.append(match.user3)
                return m
            
            if match.user2.user_id == user_id:
                m.append(match.user1)
                if match.user3:
                    m.append(match.user3)
                return m

            if match.user3 and match.user3.user_id == user_id:
                m.append(match.user1)
                m.append(match.user2)
                return m

        return None

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def get_current_match(classroom_id, curr_user):
    """
    gets the current match for the classroom,
    regardless of any new users. however,
    if there is no preexisting match,
    will make a new match and return that.
    admin-only.
    """
    if not check_admin(classroom_id, curr_user):
        return None

    # check if there is currently a match
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # verify that classroom exists
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"No classroom found with ID {classroom_id}")
            return None
        
        # if there are fewer than 2 users, return
        if len(classroom.users) < 2:
            print("There must be at least 2 users to make a match.")
            return None

        match = classroom.matches
        matches = []
        for m in match:
            m_dict = {}
            m_dict['match_id'] = m.match_id
            m_dict['complete'] = m.complete
            m_dict['user1_name'] = m.user1.user_name
            m_dict['user1_id'] = m.user1.user_id
            m_dict['user2_name'] = m.user2.user_name
            m_dict['user2_id'] = m.user2.user_id
            if m.user3:
                m_dict['user3_name'] = m.user3.user_name
                m_dict['user3_id'] = m.user3.user_id
            matches.append(m_dict)

        if matches: # a list of dicts
            print(f"matches for {classroom_id}: {matches}")
            return matches
        else:
            print(f"no matches yet for {classroom_id}, creating new")
            return make_new_match(classroom_id, curr_user)

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def make_new_match(classroom_id, curr_user):
    """
    generates a new match, but throws an error if a classroom
    has fewer than 2 members.
    if odd, will have a "pair" of 3 included
    """
    if not check_admin(classroom_id, curr_user):
        return None
    
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # verify that classroom exists
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"No classroom found with ID {classroom_id}")
            return None

        # get users, check that there are at least 2
        if len(classroom.users) < 2:
            print("Need at least 2 users in a classroom to make a match.")
            return None
        else:
            users = classroom.users

        # clear all existing matches for this classroom
        curr_matches = classroom.matches
        for match in curr_matches:
            session.delete(match)
        session.commit()

        random.shuffle(users)
        pairs = []
        start = 0
        if len(users) % 2 == 1: # odd, make a "pair" of 3
            pair = (users[0], users[1], users[2])
            pairs.append(pair)
            start = 3

        # if odd, the first pair will be the 3 group one

        for i in range(start, len(users) - 1, 2):
            pair = (users[i], users[i + 1])
            pairs.append(pair)

        for pair in pairs:
            if len(pair) == 3:
                new_match = Match(classroom_id=classroom_id, user1_id=pair[0].user_id, user2_id=pair[1].user_id, user3_id=pair[2].user_id)
            else:
                new_match = Match(classroom_id=classroom_id, user1_id=pair[0].user_id, user2_id=pair[1].user_id)
            session.add(new_match)

        session.commit()

        matches = []
        for pair in pairs:
            new_match = session.query(Match).filter_by(
                classroom_id=classroom_id,
                user1_id=pair[0].user_id,
                user2_id=pair[1].user_id
            ).first()
            match = {}
            match['match_id'] = new_match.match_id
            match['complete'] = False
            match['user1_name'] = pair[0].user_name
            match['user1_id'] = pair[0].user_id
            match['user1_email'] = pair[0].user_email
            match['user2_name'] = pair[1].user_name
            match['user2_id'] = pair[1].user_id
            match['user2_email'] = pair[1].user_email
            if len(pair) == 3:
                match['user3_name'] = pair[2].user_name
                match['user3_id'] = pair[2].user_id
                match['user3_email'] = pair[2].user_email
            matches.append(match)

        return matches

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def mark_match_complete(classroom_id, curr_user, match_id, user1_id, user2_id, user3_id=None):
    if not check_admin(classroom_id, curr_user):
        return None

    # check if there is currently a match
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # verify that classroom exists
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"No classroom found with ID {classroom_id}")
            return None
        
        # if there are fewer than 2 users, return
        if len(classroom.users) < 2:
            print("There must be at least 2 users to make a match.")
            return None

        # add 1 for score for each of the users in the match , also if there's 3 in the match
        user1 = session.query(User).filter(User.user_id == user1_id).first()
        if not user1 or user1 not in classroom.users:
            print(f"user {user1_id} not found")
            return None
        increment_user_classroom_score(classroom_id, user1.user_id, curr_user)

        user2 = session.query(User).filter(User.user_id == user2_id).first()
        if not user2 or user2 not in classroom.users:
            print(f"user {user2_id} not found")
            return None
        increment_user_classroom_score(classroom_id, user2.user_id, curr_user)

        if user3_id:
            user3 = session.query(User).filter(User.user_id == user3_id).first()
            if not user3 or user3 not in classroom.users:
                print(f"user {user3_id} not found")
                return None
            increment_user_classroom_score(classroom_id, user3.user_id, curr_user)

        match = session.query(Match).filter(Match.match_id == match_id).first()
        if not match:
            print(f"match {match_id} not found")
            return None
        match.complete = True

        session.commit()

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()


# USERS

# Admins can add_user and remove_user
# User can remove themselves

def check_user(classroom_id, user_id):
    """
    check if user_id is a user in classroom with classroom_id
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).filter(User.user_id == user_id).first()
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()

        if classroom and user and user in classroom.users:
            print(f"User {user_id} is in Classroom {classroom_id}.")
            return True
        else:
            print(f"User {user_id} is not in Classroom {classroom_id}.")
            return False

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def get_all_users(classroom_id):
    """
    get all the users in the current classroom
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()

        if classroom:
            users = [user.user_id for user in classroom.users]
            print(f"Users in Classroom {classroom_id}: {users}")
        else:
            print(f"No classroom found with ID {classroom_id}")
            return None

        session.close()
        engine.dispose()
        return users

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def add_user(classroom_id, user_id):
    """
    add an individual user to the classroom.
    for a user to add themselves.
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        user = session.query(User).filter(User.user_id == user_id).first()

        if classroom and user and user not in classroom.users:
            classroom.users.append(user)
            session.commit()
            print(f"User {user_id} added to Classroom {classroom_id}.")
            ret = {"classroom_id": classroom.classroom_id, "user_id": user_id}
        else:
            print(f"User {user_id} already in Classroom {classroom_id} or not found.")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def add_users(classroom_id, user_ids, curr_user):
    """
    adds the valid given users to the specified classroom.
    admin only.
    """
    if not check_admin(classroom_id, curr_user):
        return None
    
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # input validation for class

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"{classroom_id} is not a valid classroom id")
            return None

        # Check if all user_ids correspond to a real user
        real_users = session.query(User.user_id).filter(User.user_id.in_(user_ids)).all()
        real_admin_ids = [admin.user_id for admin in real_users]
        if set(user_ids) != set(real_admin_ids):
            missing_admins = set(user_ids) - set(real_admin_ids)
            print(f"Error: The following user IDs do not correspond to any real user: {missing_admins}")
            return None

        users = session.query(User).filter(User.user_id.in_(user_ids)).all()

        added_users = []
        for user in users:
            if classroom and user and user not in classroom.users:
                classroom.users.append(user)
                added_users.append(user.user_id)
                print(f"User {user.user_id} added to Classroom {classroom_id}.")
            else:
                print(f"User {user.user_id} already in Classroom {classroom_id} or not found.")

        if not added_users:
            ret = None
        else:
            session.commit()
            ret = {"classroom_id": classroom.classroom_id, "user_ids": added_users}
        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()


def increment_user_classroom_score(classroom_id, user_id, curr_user):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        if not check_admin(classroom_id, curr_user):
            return None

        # input validation
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"{classroom_id} is not a valid classroom id")
            return None
        
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user or user not in classroom.users:
            print(f"{user_id} is not a valid user id, or they are not in this classroom")
            return None
        
        association = session.execute(
            user_classroom_association.select().where(
                (user_classroom_association.c.user_id == user_id) &
                (user_classroom_association.c.classroom_id == classroom_id)
            )
        ).fetchone()
        
        if association:
            new_score = association.user_classroom_score + 1
            update_stmt = user_classroom_association.update().where(
                (user_classroom_association.c.user_id == user_id) &
                (user_classroom_association.c.classroom_id == classroom_id)
            ).values(user_classroom_score=new_score)
            session.execute(update_stmt)
        
        session.commit()

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()


def reset_user_classroom_score(classroom_id, user_id, curr_user):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        if not check_admin(classroom_id, curr_user):
            return None

        # input validation
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"{classroom_id} is not a valid classroom id")
            return None
        
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user or user not in classroom.users:
            print(f"{user_id} is not a valid user id, or they are not in this classroom")
            return None
        
        association = session.execute(
            user_classroom_association.select().where(
                (user_classroom_association.c.user_id == user_id) &
                (user_classroom_association.c.classroom_id == classroom_id)
            )
        ).fetchone()
        
        if association:
            new_score = 0
            update_stmt = user_classroom_association.update().where(
                (user_classroom_association.c.user_id == user_id) &
                (user_classroom_association.c.classroom_id == classroom_id)
            ).values(user_classroom_score=new_score)
            session.execute(update_stmt)

        session.commit()

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()


def get_user_classroom_score(classroom_id, user_id):
    """
    gets the user's current classroom score.
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # input validation
        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        if not classroom:
            print(f"{classroom_id} is not a valid classroom id")
            return None
        
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user or user not in classroom.users:
            print(f"{user_id} is not a valid user id, or they are not in this classroom")
            return None

        # actual SQL query because otherwise can't access table thru SQLAlchemy
        score_row = session.execute(
            user_classroom_association.select().where(
                (user_classroom_association.c.user_id == user_id) &
                (user_classroom_association.c.classroom_id == classroom_id)
            )
        ).fetchone()

        session.close()

        if score_row:
            score = score_row.user_classroom_score
            print(f"User {user_id} score: {score}")
            return score
        else:
            print(f"No score found for user {user_id} in classroom {classroom_id}")
            return None

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()


def remove_user(classroom_id, user_id, curr_user):
    """
    removes user from classroom
    """
    # only possible if you are admin OR the user
    if not check_admin(classroom_id, curr_user) and user_id != curr_user:
        return None

    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        classroom = session.query(Classroom).filter(Classroom.classroom_id == classroom_id).first()
        user = session.query(User).filter(User.user_id == user_id).first()

        if classroom and user and user in classroom.users:
            classroom.users.remove(user)
            session.commit()
            print(f"User {user_id} removed from Classroom {classroom_id}.")
            ret = {"classroom_id": classroom.classroom_id, "user_id": user_id}
        else:
            print(f"User {user_id} not in Classroom {classroom_id} or not found.")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()
