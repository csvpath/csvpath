import os
import pylightxl as xl

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos


class TestUtilBinaryCopy:
    def test_binary_copy_1(self):
        the_path = f"tests{os.sep}util{os.sep}test_resources{os.sep}xlsx{os.sep}Table_1.1_Primary_Energy_Overview.xlsx"
        new_path = (
            f"tests{os.sep}util{os.sep}test_resources{os.sep}tmp{os.sep}temp.xlsx"
        )
        nos = Nos(os.path.dirname(new_path))
        if not nos.dir_exists():
            nos.makedirs()
        nos = Nos(new_path)
        if nos.exists():
            nos.remove()
        if nos.exists():
            raise RuntimeError("Could not delete test file: {the_path}")

        with DataFileReader(the_path, mode="rb") as the_file:
            with DataFileWriter(path=new_path, mode="wb") as new_file:
                new_file.write(the_file.read())

        db = xl.readxl(fn=new_path)
        sheet = db.ws_names[0]
        assert sheet is not None
        nos = Nos(new_path)
        nos.remove()
