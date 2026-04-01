# fmt: off
import shutil
from pathlib import Path

from release_candidate_maker.release import ReleaseMaker as maker


def clear_directory(dir_path):
    path = Path(dir_path)
    if path.exists():
        shutil.rmtree(path)
        path.mkdir()
        print(f"Cleared {dir_path}")
    else:
        path.mkdir(parents=True)
        print(f"Created {dir_path}")


def run():
    clear_directory("./logs")
    clear_directory("./dist")
    clear_directory("./cache")
    clear_directory("./archive")
    clear_directory("./inputs")
    clear_directory("./transfers")

    m = maker(
        new_version_handlers=[],
        copy_to_paths=["builds"],
        copy_to_flightpath=False
    )

    m.main()


if __name__ == "__main__":
    run()

# fmt: on

