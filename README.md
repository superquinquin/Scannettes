# inventory-bl-scanner-webapp
Open source Flask webapp for delivieries and inventory management for COOP or shops with an ODOO backend.
### System of room to manage deliveries and invenotories:
<br>• Build Rooms with templates based on your incomming deliveries or product categories (inventories).
<br>• MUltiple persons can connect and interact inside the room in real time. 
<br>• A scanning system that can handle phone camera and any laser scanner device.

### A Lobby to manage your rooms:
<br>• Manage your Rooms via a lobby.
<br>• Generate QRcode of your rooms url to easily share them.
<br>• Automatically generate 2 rooms for each inventory, one for the stock and one for the aisle that can be asembled once both are finished.

### Connect the App to your Odoo database:
<br>• Easily transfert the deliveries and inventory data collect to your Odoo database.
<br>• Automatically fill up your deliveries and autovalidate them when asked to.
<br>• Generate automatically inventories and fill them up. Can autovalidate them when asked to.

# SETUP:
<br>• Git clone the repo on your server.
<br>• Generate the docker-compose file based on docker-compose.yml.template and modify it with your informations
<br>• Generate the config file based on Config.py.template  and modify it with your informations
<br>• Generate the whitelist.txt file based on whitelist.txt.template (actual admin system, might be modified later)
<br>• add admin user on the whitelist file with the following syntaxe for each lines: USER PASSWORD
<br>• ADD A folder called "volume" on the root of the repo.
<br>• CHOWN the volume folder to give rights to everyone, so the docker could write the backup and the logs into it.
```
mkdir volume
chmod 777 volume
```
<br>• Finally run the following docker compose command
```
docker-compose up --build
```

# DEV:
<br> [x] Refactor JS lobby file.
<br> [x] Refactor JS room file.
<br> [] Refactor JS camera file and make it work properly.
<br> [x] Refactor python backend.
<br> [x] Backend docstring. partly done
<br> [] mail and better Odoo db error reorientation

# Known bug:
<br>• nullification of inventories when entries and queue are empty block the client.
<br>• scanning process not handling all possible errors
<br>• ...