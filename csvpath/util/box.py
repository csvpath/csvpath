#
# just a box to put things in. initial use is
# sharing a boto3 client under "boto_s3_client".
#
class Box:
    STUFF = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        Box.STUFF = {}

    def add(self, key: str, value) -> None:
        Box.STUFF[key] = value

    def get(self, key: str):
        return Box.STUFF.get(key)
