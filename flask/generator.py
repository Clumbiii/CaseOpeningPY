from hashlib import sha512

if __name__ == '__main__':
    your_password = ""

    old_passhash = sha512(your_password.encode()).hexdigest()
    print(old_passhash)