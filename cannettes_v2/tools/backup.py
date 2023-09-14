

import time
from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL
from typing import List, Dict, Any


from cannettes_v2.odoo.deliveries import Deliveries
from cannettes_v2.odoo.lobby import Lobby
from cannettes_v2.utils import get_delay


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
        timer = Timer(delay, self.BACKUP, cache)
        timer.start()

    def BACKUP(self, cache):
        """BACKUP THREAD"""
        self.save_backup(cache, self.filename)
        self.BACKUP_RUNNER(cache)


class Update:
    def __init__(
        self,
        *,
        delta_search_purchase: List[int],
        build_update_time: List[int],
        erp: Dict[str, Any],
        **kwargs
        ) -> None:
        self.odoo = Deliveries()
        self.odoo.connect(**erp)
        self.lobby = Lobby()
        self.frequency = delta_search_purchase
        self.delta = build_update_time

    def UPDATE_RUNNER(self, cache: Dict[str, Any]):
        """THREADING and schedulding update every XXXX hours
        possibly placed under build"""
        delay = get_delay(time=self.frequency)  # time
        print(f"new update in : {delay} seconds")
        timer = Timer(delay, self.update_build, cache)
        timer.start()

    def update_build(self, cache):
        """try to update purchase list"""

        while True:
            try:
                cache = self.odoo.get_purchase(
                    self.delta, cache
                )
                cache = self.lobby.remove_historic_room(self.odoo, cache)
                cache = self.lobby.force_room_status_update(cache)
                self.UPDATE_RUNNER(cache)
                break

            except KeyError as e:
                print("__ BUILD UPDATE KEY ERROR\n", e)
                self.UPDATE_RUNNER(cache)
                break
            except Exception as e:
                print("__ BUILD UPDATE EXCEPTION\n", e)
                time.sleep(60)
