import bcrypt

# Generate bcrypt hash for testing
password = 'admin123'.encode('utf-8')
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(password, salt).decode('utf-8')
print(password_hash)