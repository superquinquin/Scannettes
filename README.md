# Scannettes
Open source Flask webapp for delivieries and inventory management for COOP with an ODOO backend.

* [Guideslines](#Contributions-Guideslines)
  * [How to contribute](#How-to-contribute)
  * [Dev setup](#Dev-setup)
  * [On what to contribute](#On-what-to-contribute)
* [Installation](#Installation)
  * [Setup](#Setup)
  * [Configuration](#Configuration)
  * [Docker-compose](#Docker-compose)
  * [Launching](#Launching)


## Contributions Guideslines
All development efforts are put into v1.0 branch, unless we need to fix a bug in production.

### How to contribute
* Create a branch based on v1.0. name your branch after the feature/fix you want to implement. prefix the branch witht the kind of change you will add ( feature/xxx ; fix/xxx ; etc.. )
* For any contribution over the python parts, make sure to use formatter such as [BLack Formatter](https://github.com/psf/black) and [Flake8 Linter](https://github.com/PyCQA/flake8)
  * Some pre-commit hooks will be added when I have the time to switch from pipenv to Poetry build.
*  Similarly for JS however, I don't know any tools nor did proper formatting myself yet.
*  Format your commits using tools such as [Commitizen](https://github.com/commitizen/cz-cli) or any equivalent tools.
*  PR must heads towards the v1.0 branch

### Dev setup

On root
```bash
poetry build
poetry install
mkdir volume
chmod 777 volume
```
when builded, you can `poetry shell` to enable the project venv.

For launching the application `bash boot.sh`.

### On what to contribute
Maybe those points will pop as Github issues if I have the time.

**Backend**
* [ ] make Odoo auto validation works for purchases.
* [ ] Config validation ( probably in CUE lang )
* [ ] maybe extension 
* [ ] maybe data validation during events

**Frontend**
* [ ] setup camera scanning

**Testing**
* Continue testing if app works properly. Soon deployment.

## Installation
### Setup
```bash
mkdir inventaire
cd inventaire
git clone https://github.com/superquinquin/inventory-bl-scanner-webapp.git
mkdir volume
chmod 777 volume
```
### Configuration
* `cannettes_configs/cannettes_config.yaml` Is the main configuration file that will be injected in the app during init time.
* `cannettes_configs/secrets.yaml` will contains all your internal admin users credentials
* `.env` will contains all api secrets and credentials for running the app. Those will be parsed and exported in `cannettes_config.yaml` at init time.

#### Scannettes configurations
Generate and fill `cannettes_configs/cannettes_config.yaml` from `cannettes_configs/cannettes_config.yaml.example`

* Flask configuration : [Flask server parameters](https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask)
* Flask Soketio configuration : [Flask SocketIo parameters](https://flask-socketio.readthedocs.io/en/latest/api.html#flask_socketio.SocketIO)
* Authentication JWT cookie configuration : [Cookie](https://flask.palletsprojects.com/en/3.0.x/api/#flask.Response.set_cookie)

For env variable that will be imported into the configuration file, annotate ${<ENV_VAR_NAME>} for the specific fields you want to apply as an env variable. The config parser will retrieve and fill the config file with the env variables

#### Env
Generate .env file after filling the différents ENV variable. It is recommended to set Odoo api credentials and SMTP server credentials as env variable. **todo: create template**

#### Create Users
```bash
python set_users_config.py
```
Following the directives of the tool for creating admin users for the applications.

This tool will generate a `cannettes_configs/secrets.yaml` containing all the admin app users.

You can whenever you want add a new users to by reusing the tool. It will automatically append this new user to the current list of users

For removing users, `nano cannettes_configs/secrets.yaml` and manually remove the users you want to delete.

### Docker-compose
Save your docker-compose file as `docker-compose.yml`. No particular inputs are needed unless you want to custumize further your docker setup.

### Launching
Once the applications is configurated:
```bash
docker-compose up --build -d
```
