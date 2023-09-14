from typing import List, Dict, Any

import time
from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL

from cannettes.packages.utils import get_delay


class Caching(object):
    def init_cache(self) -> Dict[str, Any]:
        self.cache = {
                "config": None,
                "odoo": {
                    "history": {"update_purchase": [], "update_inventory": []},
                    "purchases": {
                        "incoming": {},
                        "received": {},
                        "done": {},
                        "draft": {},
                        "pseudo-purchase": {},
                    },
                    "inventory": {
                        "type": {},  # all type of inventory, for selection purpose.
                        "ongoing": {},
                        "processed": {},
                        "done": {},
                    },
                },
                "lobby": {"rooms": {}, "users": {"admin": {}}},
        }
    
    def load_cache(self, filename: str) -> Dict[str, Any]:
        try:
            with open(filename, "rb") as f:
                self.cache = load(f)

        except FileNotFoundError or EOFError as e:
            self.cache = self.init_cache()

    def set_config(self, config: Dict[str, Any]):
        self.cache["config"] = config

    def __call__(self) -> Dict[str, Any]:
        return self.cache
    
class BackUp:
    def __init__(self, filename: str, frequency: List[int]) -> None:
        self.filename = filename
        self.frequency = frequency
    
    def save_backup(self, cache: Dict[str, Any]):
        """dump cache data dict into pickle file"""
        with open(self.filename, "wb") as f:
            dump(cache, f, protocol=HIGHEST_PROTOCOL)
            # json.dump(data, fileName)

    def BACKUP_RUNNER(self, cache: Dict[str, Any]):
        """backup thread timer runner
        select delay and prepare backup thread to run"""
        delay = get_delay(delta=self.frequency)
        print(f"new start in : {delay} seconds")
        timer = Timer(delay, self.BACKUP,cache=cache)
        timer.start()

    def BACKUP(self, cache):
        """BACKUP THREAD"""
        self.save_backup(cache, self.filename)
        self.BACKUP_RUNNER(cache)


class Update:
    def __init__(self, odoo: object, lobby: object) -> None:
        self.odoo = odoo
        self.lobby = lobby

    def UPDATE_RUNNER(self, config: object):
        """THREADING and schedulding update every XXXX hours
        possibly placed under build"""
        delay = get_delay(time=config.BUILD_UPDATE_TIME)  # time
        print(f"new update in : {delay} seconds")
        timer = Timer(delay, self.update_build)
        timer.start()

    def update_build(self):
        """try to update purchase list"""
        from cannettes import data

        while True:
            try:
                data = self.odoo.get_purchase(
                    data["config"].DELTA_SEARCH_PURCHASE, data
                )
                data = self.lobby.remove_historic_room(self.odoo, data)
                data = self.lobby.force_room_status_update(data)
                self.UPDATE_RUNNER(data["config"])
                break

            except KeyError as e:
                print("__ BUILD UPDATE KEY ERROR\n", e)
                self.UPDATE_RUNNER(data["config"])
                break
            except Exception as e:
                print("__ BUILD UPDATE EXCEPTION\n", e)
                time.sleep(60)
