from __future__ import annotations
import time
import glob
import logging
from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL
from typing import List, Dict, Any, Optional

from scannettes.odoo.deliveries import Deliveries
from scannettes.odoo.inventories import Inventories
from scannettes.odoo.lobby import Lobby
from scannettes.utils import get_delay, get_fix_delay

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
    def check_backup_file(cls, fname: str) -> bool:
        return bool(glob.glob(fname))

    @classmethod
    def initialize(
        cls, 
        method: str,
        configs: Payload,
        logging: logging,
        backup_fname: Optional[str]= None, 
        ) -> Cache:
        
        odoo_cfg = configs.get("odoo", False)
        if method == "backup" and backup_fname is None:
            raise ValueError("You must pass the backup file name for backup initialization")
        if odoo_cfg is False:
            raise KeyError("You must set the Odoo configs")

        if method == "backup":
            if backup_fname.split('.')[-1] != "pickle":
                raise ValueError("Cache currently only handle pickle files")                
            try:
                with open(backup_fname, "rb") as f:
                    data = load(f)
            except Exception as e:
                logging.error(e)
                logging.warning("Something went wrong when loading the backup... Switching to bare initialization")
                method = "bare"
                
        if method == "bare":
            data = {"deliveries": {}, "inventories": {}, "lobby": {}}
            
        lobby = Lobby(**data["lobby"])
        deliveries = Deliveries.initialize(odoo_cfg, lobby, data["deliveries"])
        inventories = Inventories.initialize(odoo_cfg, data["inventories"])
        return cls(config=configs, deliveries=deliveries, inventories=inventories, lobby=lobby)
    
    
    
    def set_config(self, configs: Payload) -> None:
        self.config = configs
    
    def to_backup(self, fname: str) -> None:
        with open(fname, "wb") as f:
            dump({
                "deliveries": self.deliveries.as_backup(),
                "inventories": self.inventories.as_backup(),
                "lobby": self.lobby.as_backup()
            }, f, protocol= HIGHEST_PROTOCOL)
            
    def set_config(self, config: Dict[str, Any]) -> None:
        self.config = config
        
    def check_integrity(self) -> bool:
        return any([attr for attr in self.__dict__ if attr is None])
    
    def update(self, payload: Payload) -> None:
        return self.__dict__.update(payload)

class BackUp:
    def __init__(self, filename: str, frequency: List[int]) -> None:
        self.filename = filename
        self.frequency = frequency
    
    def BACKUP_RUNNER(self, cache: Cache, logging:logging):
        """backup thread timer runner
        select delay and prepare backup thread to run"""
        delay = get_delay(self.frequency)
        logging.info(f"Next Backup save in {delay} secs")
        
        timer = Timer(delay, self.BACKUP, [cache, logging])
        timer.start()

    def BACKUP(self, cache: Cache, logging:logging):
        """BACKUP THREAD"""
        logging.info(f"Saving Backup into {self.filename}")
        cache.to_backup(self.filename)
        self.BACKUP_RUNNER(cache, logging)


class Update:
    def __init__(
        self,
        *,
        build_update_time: List[int],
        **kwargs
        ) -> None:
        self.time = build_update_time

    def UPDATE_RUNNER(self, cache: Dict[str, Any], logging:logging):
        delay = get_fix_delay(self.time)
        logging.info(f"Next Deliveries update in {delay} secs")
        timer = Timer(delay, self.update_build, [cache, logging])
        timer.start()

    def update_build(self, cache: Cache, logging:logging):
        logging.info(f"Starting updating Deliveries data...")
        while True:
            try:
                erp = cache.config["odoo"]["erp"]
                delta = cache.config["odoo"]["delta_search_purchase"]
                deliveries: Deliveries = cache.deliveries
                lobby: Lobby = cache.lobby
                deliveries.connect(**erp)
                deliveries.fetch_purchases(delta, lobby)
                lobby.remove_outdated_rooms()
                self.UPDATE_RUNNER(cache, logging)
                break
            except KeyError as e:
                print("__ BUILD UPDATE KEY ERROR\n", e)
                self.UPDATE_RUNNER(cache, logging)
                break
            except Exception as e:
                print("__ BUILD UPDATE EXCEPTION\n", e)
                time.sleep(60)
