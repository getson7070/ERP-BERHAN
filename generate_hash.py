from argon2 import PasswordHasher


def main() -> None:
    ph = PasswordHasher()
    password_hash = ph.hash('admin123')
    print(password_hash)


if __name__ == '__main__':
    main()