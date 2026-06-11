from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    address: str = None
    port: int = Field(
        description="Port number; coerce from string if needed.", default=None
    )
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
