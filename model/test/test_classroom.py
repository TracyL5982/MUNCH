from model.classroom import (
    get_info,
    create_classroom,
    update_classroom_name,
    update_classroom_bio,
    delete_classroom,
    get_admins,
    add_admins,
    delete_admins,
)

# Helper function to print the details of a classroom
def print_classroom_details(classroom_id):
    classroom_info = get_info(classroom_id)
    if classroom_info:
        print(f"Classroom Info: {classroom_info}")
    else:
        print(f"Classroom with ID {classroom_id} not found.")

# Test get_info
print("Testing get_info...")
print_classroom_details(7)  # Assuming a classroom with ID 1 exists

# Test create_classroom
print("\nTesting create_classroom...")
classroom_name = "New Classroom"
classroom_bio = "This is a new classroom created for testing."
admin_ids = [1,2]  # Assuming a user with ID 1 exists and is an admin
new_classroom = create_classroom(admin_ids, classroom_name, classroom_bio)
if new_classroom:
    print(f"New Classroom: {new_classroom}")
print_classroom_details(8)
# Test update_classroom_name
print("\nTesting update_classroom_name...")
updated_name = "Updated Classroom Name"
update_result = update_classroom_name(new_classroom['classroom_id'], updated_name)
print(f"Update Result: {update_result}")

# Test update_classroom_bio
print("\nTesting update_classroom_bio...")
updated_bio = "Updated Classroom Bio"
update_bio_result = update_classroom_bio(new_classroom['classroom_id'], updated_bio)
print(f"Update Bio Result: {update_bio_result}")
# Test get_admins
print("\nTesting get_admins...")
admins = get_admins(new_classroom['classroom_id'])
print(f"Admins: {admins}")

# Test add_admins
print("\nTesting add_admins...")
add_admins_result = add_admins(new_classroom['classroom_id'], [3])  # Assuming a user with ID 2 exists
print(f"Add Admins Result: {add_admins_result}")

# Test delete_admins
print("\nTesting delete_admins...")
delete_admins_result = delete_admins(new_classroom['classroom_id'], [2])
print(f"Delete Admins Result: {delete_admins_result}")

# Test delete_classroom
print("\nTesting delete_classroom...")
delete_result = delete_classroom(new_classroom['classroom_id'])
print(f"Delete Result: {delete_result}")

