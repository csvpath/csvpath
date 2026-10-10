import traceback
from importlib.metadata import version, PackageNotFoundError

from openlineage.client.facet_v2 import processing_engine_run


class EngineUtility:
    @classmethod
    def engine_facet(cls) -> str:
        v = ""
        try:
            v = version("csvpath")
        except PackageNotFoundError:
            print(traceback.format_exc())
        except Exception:
            ...
        pe = processing_engine_run.ProcessingEngineRunFacet(
            name="CsvPath Framework", version=f"{v};OL.v2"
        )
        return pe
