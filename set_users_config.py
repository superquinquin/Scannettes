from yaml import SafeLoader, load, dump
from hashlib import sha256
import os
import getpass

def set_user_config():
    secrets = {"users": {}}
    path = os.path.dirname(__file__)
    root = os.listdir(path) 
    if "cannettes_configs" not in root:
        raise FileExistsError("You must create a cannettes_confgs folder")
    
    config_path = f"{path}/cannettes_configs"
    secrets_path = f"{config_path}/secrets.yaml"
    config = os.listdir(config_path)
    if "secrets.yaml" in config:
        secrets = load(open(secrets_path,"r"), SafeLoader)
    
    onemore = True
    while onemore:
        print(" | Registering user...")
        username = input("Username: ")
        password = sha256(getpass.getpass("Password: ").encode("utf-8")).hexdigest()
        payload = {"username": username, "password": password, "authorization": [""]}
        while secrets["users"].get(username):
            print('... this username already exist. please enter another username')
            username = input("Username: ")
        secrets["users"][username] = payload
        
        more = None
        while more not in ["y", "n"]:
            more = input("Continue ? (y/N):  ").lower()
            
        if more == "n":
            onemore = False
    
    print(f"Saving secrets into {secrets_path} !")
    with open(secrets_path, "w") as f:
        dump(secrets, f)   




if __name__ == "__main__":
    set_user_config()