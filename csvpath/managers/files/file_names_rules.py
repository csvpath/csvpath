class FileNamesRules:
    @staticmethod
    def is_legal_file_name(name: str) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        if name.strip() == "":
            raise ValueError("Name cannot be empty")
        if name.find("/") > -1 or name.find("\\") > -1:
            raise ValueError(
                f"Not a legal name: {name}. Path seperators are not allowed."
            )
        if name.find(".") > -1:
            raise ValueError(f"Not a legal name: {name}. Periods are not allowed.")
        if name.find("$") > -1:
            raise ValueError(f"Not a legal name: {name}. Dollarsigns are not allowed.")
        if name.find("#") > -1:
            raise ValueError(f"Not a legal name: {name}. Hashmarks are not allowed.")

    @staticmethod
    def make_clean_file_name(fname: str) -> str:
        fname = fname.replace("?", "_")
        fname = fname.replace("&", "_")
        fname = fname.replace("=", "_")
        return fname
