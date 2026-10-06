from csvpath.util.config import Config
from csvpath.util.class_loader import ClassLoader
from csvpath.util.class_loader import ClassLoadingError


class OpenLineageListenerProxy:
    @classmethod
    def _load(cls, *, config: Config, sig: str):
        if config is None:
            raise ValueError("Config cannot be None")
        if sig is None:
            raise ValueError("Sig cannot be None")
        groups = config.get(section="listeners", name="groups")
        version = config.get(section="openlineage", name="version", default=1)
        version = int(version)
        while True:
            data = {"version": version}
            s = sig.format_map(data)
            inst = ClassLoader.try_load(s, [], {"config": config})
            if isinstance(inst, Exception):
                config.logger.error(inst)
                config.logger.error(
                    f"Cannot load {s} in groups {groups} with version: {version} and config: {config}: {type(inst)}"
                )
            elif inst:
                return inst
            version -= 1
            if version == 0:
                raise ClassLoadingError(f"Cannot find version {version} as {sig}")
