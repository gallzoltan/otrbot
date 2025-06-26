import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    system: str
    url: str
    username: str
    password: str
    logs_path: str
    env: str
    
    @classmethod
    def from_env(cls, env: Optional[str] = None) -> 'Config':
        env = env or os.getenv("ENV", "dev")
        
        if env == "dev":
            url = os.getenv("OTR_EDU_URL")
            username = os.getenv("OTR_EDU_USERNAME")
            password = os.getenv("OTR_EDU_PASSWORD")
        else:
            url = os.getenv("OTR_URL")
            username = os.getenv("OTR_USERNAME")
            password = os.getenv("OTR_PASSWORD")
            
        return cls(
            system=os.getenv("SYSTEM", "windows"),
            url=url,
            username=username,
            password=password,
            logs_path=os.getenv("OTR_LOGS_PATH", "./logs/otr.log"),
            env=env
        )