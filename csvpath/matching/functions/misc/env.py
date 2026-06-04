from typing import Any
from ..function_focus import ValueProducer
from ..args import Args
from csvpath.util.config_env import ConfigEnv


class Env(ValueProducer):
    def check_valid(self) -> None:  # pylint: disable=W0246
        self.description = [
            self.wrap(
                """\
                Provides access to the env var source. The source may be the OS env vars
                (config.ini's [config] env_var_source setting == "env") or the project env.json
                file. In a FlightPath Server project the source is always the JSON file.

                If the name is not an env var key the return is None
                """
            ),
        ]
        self.name_qualifier = False
        self.args = Args(matchable=self)
        self.args.argset(1).arg(name="name", types=[None, Any], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()  # pylint: disable=W0246

    def _produce_value(self, skip=None) -> None:
        name = self._value_one(skip=skip)
        if name is None or name.strip() == "":
            return
        self.value = ConfigEnv(config=self.matcher.csvpath.config).get_from_env(
            name=name
        )

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
