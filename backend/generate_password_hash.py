import sys
import bcrypt

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_password_hash.py <mot_de_passe>")
        sys.exit(1)

    password_bytes = sys.argv[1].encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    print(hashed.decode("utf-8"))
