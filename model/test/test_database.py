from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.database import Base, User, Classroom, Feed  # Import your classes here

# Create an in-memory SQLite database
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Creating users
user1 = User(user_name="Alice", user_contact="alice@example.com")
user2 = User(user_name="Bob", user_contact="bob@example.com")
user3 = User(user_name="Charlie", user_contact="charlie@example.com")

# Add users to the session
session.add(user1)
session.add(user2)
session.add(user3)

# Commit to save users to the database
session.commit()

# Create a classroom
classroom = Classroom(classroom_name="Biology 101", classroom_bio="Intro to Biology")

# Add users to the classroom
classroom.users.append(user1)
classroom.users.append(user2)
classroom.users.append(user3)

# Assign admin
classroom.admins.append(user2)

# Optionally, create a feed and associate with the classroom
feed = Feed()
classroom.feed = feed

# Add the classroom (and feed) to the session
session.add(classroom)

# Commit to save the classroom to the database
session.commit()

# Query and print to verify
for user in session.query(User).all():
    print(f"User: {user.user_name}")

for classroom in session.query(Classroom).all():
    print(f"\nClassroom: {classroom.classroom_name}")
    for user in classroom.users:
        print(f" - User in class: {user.user_name}")
    for admin in classroom.admins:
        print(f" - Admin in class: {admin.user_name}")

# Close the session
session.close()
