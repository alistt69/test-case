import random


def generate_captcha():
    operation_choice = random.randint(0, 1)
    operation = '+' if operation_choice == 0 else '-'

    first_number = random.randint(10, 99)
    second_number = random.randint(10, 99)

    result = str(first_number) + operation + str(second_number)

    return result

