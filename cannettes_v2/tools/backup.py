import time
import glob
from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL
from typing import List, Dict, Any, Optional

from cannettes_v2.odoo.deliveries import Deliveries
from cannettes_v2.odoo.inventories import Inventories
from cannettes_v2.odoo.lobby import Lobby
from cannettes_v2.utils import get_delay

Payload = Dict[str, Any]

class Cache(object):
    config: Dict[str, Any]
    deliveries: Deliveries
    inventories: Inventories
    lobby: Lobby
    
    def __init__(
        self, 
        *, 
        config: Optional[Dict[str, Any]]= None, 
        deliveries: Optional[Deliveries]= None, 
        inventories: Optional[Inventories]= None, 
        lobby: Optional[Lobby]= None
        ) -> None:
        self.config = config
        self.deliveries = deliveries
        self.inventories = inventories
        self.lobby = lobby

    @classmethod
    def initialize(cls, backend: Optional[Dict[str, Any]]= None, backup: Optional[str]= None):
        cache = None
        if backend is None and backup is None:
            raise ValueError("you must pack the backend or the backup for initialization")
        if backend and backup:
            raise ValueError("you must choose between backend and backup initialization")
        
        if backup:
            if bool(glob.glob(backup)) is False:
                raise ValueError("your backup file has not been found")
            if backup.split('.')[-1] != "pickle":
                raise ValueError("Cache currently only handle pickle files")
            with open(backup, "rb") as f:
                cache = load(f)

        elif backend:
            cache = cls(**backend)
        return cache

    def to_backup(self, fname: str) -> None:
        with open(fname, "wb") as f:
            dump(self, f, protocol= HIGHEST_PROTOCOL)
            
    def set_config(self, config: Dict[str, Any]) -> None:
        self.config = config
        
    def check_integrity(self) -> bool:
        return any([attr for attr in self.__dict__ if attr is None])
    
    def update(self, payload: Payload) -> None:
        for k, v in payload.items():
            current = getattr(self, k, None)
            if current is None:
                raise KeyError(f"{self} : {k} attribute doesn't exist")
            if type(current) != type(v) and current is not None:
                raise TypeError(
                    f"{self} : field {k} value {v} ({type(v)}) does not match current type : {type(current)}"
                )
            setattr(self, k, v)

class BackUp:
    def __init__(self, filename: str, frequency: List[int]) -> None:
        self.filename = filename
        self.frequency = frequency
    
    def BACKUP_RUNNER(self, cache: Cache):
        """backup thread timer runner
        select delay and prepare backup thread to run"""
        delay = get_delay(delta=self.frequency)
        print(f"new start in : {delay} seconds")
        timer = Timer(delay, self.BACKUP, cache)
        timer.start()

    def BACKUP(self, cache: Cache):
        """BACKUP THREAD"""
        cache.to_backup(self.filename)
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

    def update_build(self, cache: Cache):
        """try to update purchase list"""

        while True:
            try:
                deliveries = cache.get("deliveries")
                lobby = cache.get("lobby")
                deliveries.fetch_purchases(cache)
                lobby.remove_outdated_rooms()
                self.UPDATE_RUNNER(cache)
            except KeyError as e:
                print("__ BUILD UPDATE KEY ERROR\n", e)
                self.UPDATE_RUNNER(cache)
                break
            except Exception as e:
                print("__ BUILD UPDATE EXCEPTION\n", e)
                time.sleep(60)
