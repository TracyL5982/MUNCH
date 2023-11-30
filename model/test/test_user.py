from model.user import (
    get_user_info,
    create_user,
    update_user_name,
    update_user_email,
    update_user_phone,
    delete_user
)

# Assuming we have a user with ID 1 in the database for testing
test_user_id = 1

# Test get_user_info
print("Testing get_user_info...")
user_info = get_user_info(test_user_id)
print("User Info:", user_info)

# Test create_user
print("\nTesting create_user...")
new_user = create_user("Test User", "testuser@example.com", "1234567890", "abcd")
print("New User:", new_user['user_id'])

# Assuming new_user is not None and contains 'user_id'
if new_user:
    new_user_id = new_user['user_id']

    # Test update_user_name
    print("\nTesting update_user_name...")
    updated_name = update_user_name(new_user_id, "Updated Test User")
    print("Updated User Name:", updated_name)

    # Test update_user_email
    print("\nTesting update_user_email...")
    updated_email = update_user_email(new_user_id, "updateduser@example.com")
    print("Updated User Email:", updated_email)

    # Test update_user_phone
    print("\nTesting update_user_phone...")
    updated_phone = update_user_phone(new_user_id, "0987654321")
    print("Updated User Phone:", updated_phone)

    # Finally, test delete_user
    print("\nTesting delete_user...")
    deletion_result = delete_user(new_user_id)
    print("Deletion Result:", deletion_result)

