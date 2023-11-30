from sys import argv, stderr, exit
from sqlite3 import connect as sqlite_connect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from model.database import Base, Feed, Classroom, User
from database import Base, Feed, Classroom, User


# -----------------------------------------------------------------------

"""TEST TO INITIATE DB"""

DATABASE_NAME = 'model/lunchtag.sqlite'


def main():

    if len(argv) != 1:
        print('Usage: python3 create.py', file=stderr)
        exit(1)

    try:
        engine = create_engine('sqlite://',
                               creator=lambda: sqlite_connect(
                                   'file:' + DATABASE_NAME + '?mode=rwc', uri=True))

        Session = sessionmaker(bind=engine)
        session = Session()

        # Base.metadata.drop_all(engine)
        # Base.metadata.create_all(engine)

        # # ---------------------------------------------------------------

        # user = User(user_id=0, user_name="Grace Bu", user_email="grace.bu@yale.edu", user_phone="abc")
        # session.add(user)
        # # user = User(user_id=1, user_name="Tracy Li", user_email="xinran.li@yale.edu", user_phone="abc")
        # # session.add(user)
        # # user = User(user_id=2, user_name="Sarah Wang", user_email="sarah.wang@yale.edu", user_phone="abc")
        # # session.add(user)
        # # user = User(user_id=3, user_name="Sianna Xiao", user_email="sianna.xiao@yale.edu", user_phone="abc")
        # # session.add(user)
        # # user = User(user_id=4, user_name="John Doe", user_email="john_doe@gmail.com", user_phone="abc")
        # # session.add(user)
        # session.commit()

        # # ---------------------------------------------------------------

        # classroom = Classroom(classroom_id=0, classroom_name="Coding Club", classroom_bio="Organization for students enthusiastic about programming")
        # session.add(classroom)
        # classroom.admins.append(user)
        # session.commit()

        # ---------------------------------------------------------------

        # CHECK THAT IT WORKED

        for classroom in session.query(Classroom).all():
            print(classroom.classroom_name, classroom.classroom_bio)
            for user in classroom.admins:
                print(user.user_name)
            print()

        session.close()
        engine.dispose()

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)

# -----------------------------------------------------------------------


if __name__ == '__main__':
    main()
