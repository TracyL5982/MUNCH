import model.classroom as classroom
import model.user as user

def main():
    classroom_num = 0
    user_ids = [1, 2, 3, 4, 5]

    for user in user_ids:
        classroom.add_user(classroom_num, user)
    
    print(classroom.make_new_match(classroom_num))

    print(classroom.update_classroom_name(0, "Grace's class"))
    


if __name__ == '__main__':
    main()
