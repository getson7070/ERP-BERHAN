from argon2 import PasswordHasher
from getpass import getpass


def main() -> None:
    ph = PasswordHasher()
    password = getpass("Password to hash: ")
    password_hash = ph.hash(password)
    print(password_hash)


if __name__ == "__main__":
    main()


