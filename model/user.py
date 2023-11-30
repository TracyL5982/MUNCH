import os
from sys import argv, stderr, exit
from sqlite3 import connect as sqlite_connect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.database import User, user_classroom_association, admin_classroom_association, DATABASE_NAME

"""
user module for functions relating to users
"""
"""
Functions:
    get_user_info(user_id):
        return {"user_name": user.user_name,
                    "user_email": user.user_email,
                    "user_phone": user.user_phone,
                    "score": user.score, "classrooms": classrooms,
                    "admin_classrooms": admin_classrooms}

    create_user(name, email, phone):
        return {"user_id": created_user_id,
                "user_name": name}

    update_user_name(user_id, name):
        return {"user_id": user_id,
                "user_name": name}

    update_user_email(user_id, email):
        return {"user_id": user_id,
                "user_email": email}

    update_user_phone(user_id, phone):
        return{"user_id": user_id,
            "user_phone": phone}

   delete_user(user_id):
     return user_id
"""


engine = create_engine('sqlite://',
                       creator=lambda: sqlite_connect(
                           'file:' + DATABASE_NAME + '?mode=rw', uri=True))

def get_user_info(user_id):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).filter_by(user_id=user_id).first()

        classrooms = (session.query(user_classroom_association.c.classroom_id)
                         .filter(user_classroom_association.c.user_id==user_id)
                         .all()
                         )

        admin_classrooms = (session.query(admin_classroom_association.c.classroom_id)
                         .filter(admin_classroom_association.c.user_id==user_id)
                         .all()
                         )

        if not user:
            return None
        else:
            return {"user_name": user.user_name,
                    "user_email": user.user_email,
                    "user_phone": user.user_phone,
                    "score": user.score, "classrooms": classrooms,
                    "admin_classrooms": admin_classrooms,
                    "user_id": user.user_id}

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def create_user(name, email, phone, password):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        #user name and email is required to create a new user, phone optional?
        if not name :
            print ("Need to enter a user name to create a new user")
            session.close()
            engine.dispose()
            return None

        if not email:
            print ("Need to enter a user email to create a new user")
            session.close()
            engine.dispose()
            return None

        new_user = User(user_name=name, user_email=email, user_phone=phone)
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        created_user_id = new_user.user_id

        return {"user_id": created_user_id,
                "user_name": name}

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def get_user_by_email(email):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # Query for the user by email
        user = session.query(User).filter_by(user_email=email).first()
        return user
    except Exception as ex:
        print(ex, file=stderr)
    finally:
        session.close()

def get_user_by_name(name):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # Query for the user by name
        user = session.query(User).filter_by(user_name=name).first()
        return user
    except Exception as ex:
        print(ex, file=stderr)
    finally:
        session.close()

def update_user_name(user_id, name):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.user_name = name
            session.commit()
            print(f"User {user_id} name updated successfully.")
            ret = {"user_id": user_id,
                   "user_name": name}
        else:
            print(f"No user found with ID {user_id}")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def update_user_email(user_id, email):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.user_email = email
            session.commit()
            print(f"User {user_id} email updated successfully.")
            ret = {"user_id": user_id, "user_email": email}
        else:
            print(f"No user found with ID {user_id}")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)

    finally:
        session.close()

def update_user_phone(user_id, phone):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.user_phone = phone
            session.commit()
            print(f"User {user_id} phone updated successfully.")
            ret = {"user_id": user_id, "user_phone": phone}
        else:
            print(f"No user found with ID {user_id}")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()

def delete_user(user_id):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"User {user_id} deleted successfully.")
            ret = user_id
        else:
            print(f"No user found with ID {user_id}")
            ret = None

        return ret

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
    finally:
        session.close()


def _test(user_id):
    print(get_user_info(user_id))

if __name__ == '__main__':
    _test(0)

