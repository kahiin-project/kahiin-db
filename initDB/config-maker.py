import sys, configparser, hashlib, io
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from os import path

relative_path = path.dirname(__file__)
config_path = path.join(relative_path,"..", "config.ini")


# Create config file
if len(sys.argv) > 9:
    password = sys.argv[1]
    host = sys.argv[2]
    key = sys.argv[9]
    user = sys.argv[3]
    database = sys.argv[4]
    email = sys.argv[5]
    email_password = sys.argv[6]
    smtp_server = sys.argv[7]
    smtp_port = sys.argv[8]
    
    # Créer la configuration
    config = configparser.ConfigParser()
    config.add_section("Database")
    config.set("Database", "password", password)
    config.set("Database", "host", host)
    config.set("Database", "user", user)
    config.set("Database", "database", database)
    config.add_section("Email")
    config.set("Email", "email", email)
    config.set("Email", "password", email_password)
    config.add_section("SMTP")
    config.set("SMTP", "server", smtp_server)
    config.set("SMTP", "port", smtp_port)
    
    # Écrire la configuration dans une chaîne
    
    config_string = io.StringIO()
    config.write(config_string)
    config_content = config_string.getvalue()
    config_string.close()
    key_bytes = hashlib.sha256(key.encode()).digest()[:16]  
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    
    # Chiffrer le contenu
    encrypted_data = cipher.encrypt(pad(config_content.encode(), AES.block_size))
    
    # Écrire l'IV et le contenu chiffré dans le fichier
    with open(config_path, "wb") as f:
        f.write(iv + encrypted_data)
    
    print("Config file created successfully")

else:
    print("Please provide all the necessary arguments")
    print("Usage: python config-maker.py <db_password> <db_host> <user> <database> <email> <email_password> <smtp_server> <smtp_port> <encryption_key>")
    sys.exit(1)
