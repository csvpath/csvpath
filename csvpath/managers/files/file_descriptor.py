from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from csvpath.managers.server_config import ServerConfig

"""
class ServerConfig(BaseModel):
    address: str = Field(description="Hostname or IP address of the server.")
    port: int = Field(description="Port number; coerce from string if needed.", default=None)
    username: str = Field(description="Login username (may be an env-var name).")
    password: str = Field(description="Login password (may be an env-var name).")

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


class OnArrival(BaseModel):
    named_paths_group: Optional[str] = Field(
        default=None,
        description="The named-paths group to associate with this file.",
    )
    run_method: Optional[str] = Field(
        default=None,
        description="The method to invoke on arrival (e.g. 'collect_paths').",
    )

    model_config = {"extra": "allow"}


class Config(BaseModel):
    """
    contents of a named-file's definition.json.
    e.g.:
        {
            "template": ":0/:3/my/:filename",
            "on_arrival": {
                "named_paths_group": "order validations",
                "run_method": "collect_paths"
            },
            sources: {
                "a": {
                    "address":"localhost",
                    "port":22,
                    "username":"foo",
                    "password":"bar"
                }
            }
        }
    """

    template: Optional[str] = Field(
        default=None,
        description="Path template string for this named file.",
    )
    on_arrival: Optional[OnArrival] = None
    sources: Optional[dict[str, ServerConfig]] = None

    model_config = {"extra": "allow"}
