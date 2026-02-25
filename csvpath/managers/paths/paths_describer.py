import traceback
import json
from typing import NewType
from typing import Optional

from csvpath.util.nos import Nos
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.references.reference_parser import ReferenceParser

from pydantic import BaseModel

NamedPathsName = NewType("NamedPathsName", str)


class Scripts(BaseModel):
    on_complete_all: Optional[str] = None
    on_complete_valid: Optional[str] = None
    on_complete_invalid: Optional[str] = None
    on_complete_error: Optional[str] = None


class Webhooks(BaseModel):
    on_complete_all: Optional[str] = None
    on_complete_invalid: Optional[str] = None
    on_complete_valid: Optional[str] = None
    on_complete_error: Optional[str] = None
    all_url: Optional[str] = None
    valid_url: Optional[str] = None
    invalid_url: Optional[str] = None
    error_url: Optional[str] = None


class GroupConfig(BaseModel):
    template: Optional[str] = None
    scripts: Optional[Scripts] = None
    webhooks: Optional[Webhooks] = None


class Config(BaseModel):
    groups: Optional[dict[str, GroupConfig]] = None


class NamedPathsDescriber:

    README = "README.md"
    DEFAULT_README = "# Named-Paths Documentation\n\n"
    JSON_FILE = "definition.json"

    TEMPLATE = "template"
    CONFIG = "_config"
    SCRIPTS = "scripts"
    # ON_COMPLETE_ALL_SCRIPT = "on_complete_all_script"
    # ON_COMPLETE_VALID_SCRIPT = "on_complete_valid_script"
    # ON_COMPLETE_ERROR_SCRIPT = "on_complete_error_script"

    def __init__(self, paths_manager) -> None:
        self.paths_manager = paths_manager

    def _name_for_name(self, name: NamedPathsName) -> str:
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.paths_manager.csvpaths)
            return ref.root_major
        return name

    # ========== JSON ============

    def store_json(self, name: NamedPathsName, j: dict) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.paths_manager.named_paths_home(name)
        #
        # validate the config structure
        #
        if self.CONFIG in j:
            GroupConfig(**j[self.CONFIG])
        p = Nos(home).join(self.JSON_FILE)
        with DataFileWriter(path=p) as writer:
            json.dump(j, writer.sink, indent=2)

    def get_json(self, name: NamedPathsName) -> dict:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.paths_manager.named_paths_home(name)
        path = Nos(home).join(self.JSON_FILE)
        nos = Nos(path)
        if nos.exists() is False:
            self.store_json(name, {})
        with DataFileReader(path) as file:
            j = json.load(file.source)
            #
            # validate config structure
            #
            if self.CONFIG in j:
                GroupConfig(**j[self.CONFIG])
            return j

    # ========== Config ============

    def store_config(self, name: NamedPathsName, j: dict | GroupConfig) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        _ = self.get_json(name)
        config = None
        c = _.get(self.CONFIG)
        if c is None:
            config = Config()
        else:
            config = Config(**c)
        if config.groups is None:
            config.groups = {}
        if not hasattr(j, "model_dump"):
            gc = GroupConfig(**j)
            config.groups[name] = gc
        else:
            config.groups[name] = j
        _[self.CONFIG] = config.model_dump()
        self.store_json(name, _)

    def get_config(self, name: NamedPathsName) -> GroupConfig:
        if name is None:
            raise ValueError("Name cannot be None")
        _ = self.get_json(name)

        cfg = _.get(self.CONFIG)
        if cfg:
            cfg = Config(**cfg)
        else:
            cfg = Config()
        ret = None
        if cfg.groups is None:
            ret = GroupConfig()
        elif name not in cfg.groups:
            ret = GroupConfig()
        else:
            ret = cfg.groups[name]
        return ret

    # ========== Templates ============

    def get_template(self, name: NamedPathsName) -> str:
        if name is None:
            raise ValueError("Name cannot be None")
        config = self.get_config(name)
        return config.template

    def store_template(self, name: NamedPathsName, template: str) -> None:
        config = self.get_config(name)
        config.template = template
        self.store_config(name, config)

    # ========== MD file ============

    def store_readme(
        self, *, name: NamedPathsName, readme: str, overwrite: bool = True
    ) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.paths_manager.named_paths_home(name)
        p = Nos(home).join(self.README)
        if overwrite is False and Nos(p).exists():
            return
        with DataFileWriter(path=p) as writer:
            writer.write(readme)

    def get_readme(self, name: NamedPathsName) -> dict:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.paths_manager.named_paths_home(name)
        path = Nos(home).join(self.README)
        nos = Nos(path)
        if nos.exists() is False:
            self.store_readme(name, self.DEFAULT_README)
        with DataFileReader(path) as file:
            return file.read()

    # ========== scripts ============

    def store_script_for_paths(
        self,
        *,
        name: NamedPathsName,
        script_name: str,
        script_type: str = "all",
        text: str = None,
    ) -> None:
        if script_name is None:
            raise ValueError("script name cannot be None")
        if script_type is None:
            raise ValueError("script type cannot be None")
        t = script_type.strip().lower()
        scripts = self.get_scripts(name)
        if t.find("all") > -1:
            scripts.on_complete_all = script_name
        elif t.find("invalid") > -1:
            scripts.on_complete_invalid = script_name
        elif t.find("valid") > -1:
            scripts.on_complete_valid = script_name
        elif t.find("error") > -1:
            scripts.on_complete_error = script_name
        else:
            raise ValueError(f"Unknown script type: {t}")
        self.store_scripts(name, scripts)
        #
        # if we have the text of the script, store that too
        #
        if text is not None:
            #
            # if the user configured a shell we'll use it to add a shebang.
            #
            if not text.startswith("#!"):
                s = self.paths_manager.csvpaths.config.get(
                    section="scripts", name="shell"
                )
                if s is not None:
                    text = f"#!{s}\n{text}"
            script_file = Nos(self.paths_manager.named_paths_home(name)).join(
                script_name
            )
            try:
                with DataFileWriter(path=script_file, mode="wb") as file:
                    file.write(text)
            except Exception as e:
                msg = f"Could not store script at {script_file}: {e}"
                self.paths_manager.csvpaths.logger.error(e)
                self.paths_manager.csvpaths.error_manager.handle_error(
                    source=traceback.format_exc(), msg=msg
                )
                if self.paths_manager.csvpaths.ecoms.do_i_raise():
                    raise RuntimeError(msg)
                return

    def store_scripts(self, name: NamedPathsName, s: Scripts) -> None:
        config = self.get_config(name)
        config.scripts = s
        self.store_config(name, config)

    def get_scripts(self, name: NamedPathsName) -> Scripts:
        config = self.get_config(name)
        s = config.scripts
        if s is None:
            return Scripts()
        return s

    def get_scripts_for_paths(self, name: NamedPathsName) -> list:
        s = self.get_scripts(name)
        lst = []
        if s.on_complete_all:
            lst.append(("on_complete_all", s.on_complete_all))
        if s.on_complete_valid:
            lst.append(("on_complete_valid", s.on_complete_valid))
        if s.on_complete_invalid:
            lst.append(("on_complete_invalid", s.on_complete_invalid))
        if s.on_complete_error:
            lst.append(("on_complete_error", s.on_complete_error))
        return lst

    #
    # given a named-paths name and one of the four types of scripts, returns the
    # full filesystem path to the script file. the four types of scripts are:
    #    - on_complete_all_script
    #    - on_complete_errors_script
    #    - on_complete_valid_script
    #    - on_complete_invalid_script
    # script_type in ["all", "invalid", "valid", "error"] will also be recognized.
    #
    def get_script_path_for_paths(
        self, *, name: NamedPathsName, script_type: str
    ) -> str:
        if name is None:
            raise ValueError("Name cannot be None")
        if script_type is None:
            raise ValueError("Script type cannot be None")
        t = script_type.strip().lower()
        scripts = self.get_scripts(name)
        r = None
        if t.find("all") > -1:
            r = scripts.on_complete_all
        elif t.find("invalid") > -1:
            r = scripts.on_complete_invalid
        elif t.find("valid") > -1:
            r = scripts.on_complete_valid
        elif t.find("error") > -1:
            r = scripts.on_complete_error
        else:
            raise ValueError(f"Unknown script type: {t}")
        return Nos(self.paths_manager.named_paths_home(name)).join(r)

    #
    # gets the text of the script indicated by named-paths name and script type
    #
    def get_script_for_paths(self, *, name: NamedPathsName, script_type: str) -> str:
        path = self.get_script_path_for_paths(name=name, script_type=script_type)
        if path is None:
            raise ValueError(f"Script path for {script_type} is not found in {name}")
        nos = Nos(path)
        if nos.exists():
            with DataFileReader(path) as file:
                return file.read()
        else:
            raise ValueError(f"Script {path} not found")

    # ========== scripts ============

    def store_webhooks(self, name: NamedPathsName, w: Webhooks) -> None:
        config = self.get_config(name)
        config.webhooks = w
        self.store_config(name, config)

    def get_webhooks(self, name: NamedPathsName) -> Webhooks:
        config = self.get_config(name)
        w = config.webhooks
        if w is None:
            return Webhooks()
        return w
