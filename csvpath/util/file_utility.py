import psutil
import os

class FileUtility:
    @classmethod
    def open_files(cls, name:str):
        for proc in psutil.process_iter(['pid', 'name']):
            _n = proc.info['name'].lower()
            if name in _n:
                return proc.open_files()

    @classmethod
    def file_descriptors(cls, name:str):
        ds = []
        try:
            files = cls.open_files(name)
            if files:
                for pfile in files:
                    ds.append(pfile.fd)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as ex:
            pass
        return ds

    @classmethod
    def open_file_count(cls) -> int:
        p = psutil.Process(os.getpid())
        fs = p.open_files()
        return -1 if not fs else len(fs)


