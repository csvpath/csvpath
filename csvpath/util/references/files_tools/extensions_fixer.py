import os
from csvpath.util.references.reference_parser import ReferenceParser


class ExtensionsFixer:
    @classmethod
    def replace_dot(cls, file) -> str:
        i = file.find(".")
        j = i + 1
        file = f"{file[0:i]}_{file[j:]}"
        return file
