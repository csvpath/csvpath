from typing import Optional
from pydantic import BaseModel, model_validator
from csvpath.managers.server_config import ServerConfig


class Scripts(BaseModel):
    on_complete_all: Optional[str] = None
    on_complete_valid: Optional[str] = None
    on_complete_invalid: Optional[str] = None
    on_complete_error: Optional[str] = None


class Header(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class Webhook(BaseModel):
    url: Optional[str] = None
    payload: Optional[str] = None
    headers: list[Header] = []


class Webhooks(BaseModel):
    on_complete_all: Optional[Webhook] = None
    on_complete_invalid: Optional[Webhook] = None
    on_complete_valid: Optional[Webhook] = None
    on_complete_error: Optional[Webhook] = None


class Transfer(BaseModel):
    file: Optional[str] = None
    transfer_to: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def parse_single_key_dict(cls, data):
        if isinstance(data, dict) and "file" not in data and "transfer_to" not in data:
            items = list(data.items())
            if len(items) == 1:
                return {"file": items[0][0], "transfer_to": items[0][1]}
        return data


class Transfers(BaseModel):
    on_complete_all: Optional[list[Transfer]] = None
    on_complete_invalid: Optional[list[Transfer]] = None
    on_complete_valid: Optional[list[Transfer]] = None
    on_complete_error: Optional[list[Transfer]] = None


class GroupTransfers(BaseModel):
    path_transfers: Optional[dict[str, Transfers]] = None

    @model_validator(mode="before")
    @classmethod
    def wrap_dict(cls, data):
        if isinstance(data, dict) and "path_transfers" not in data:
            return {"path_transfers": data}
        return data


"""
class ServerConfig(BaseModel):
    address: str = None
    port: int = Field(description="Port number; coerce from string if needed.", default=None)
    username: str = None
    password: str = None

    @field_validator("port", mode="before")
    @classmethod
    def coerce_port(cls, v: object) -> int:
        try:
            return int(v)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"port must be an integer or a numeric string, got {v!r}"
            ) from e

    model_config = {"extra": "forbid"}
"""


class GroupConfig(BaseModel):
    template: Optional[str] = None
    scripts: Optional[Scripts] = None
    webhooks: Optional[Webhooks] = None
    transfers: Optional[GroupTransfers] = None
    destinations: Optional[dict[str, ServerConfig]] = None


class Config(BaseModel):
    groups: Optional[dict[str, GroupConfig]] = None
