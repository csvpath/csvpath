import threading
import unittest
from csvpath.util.box import Box


class TestUtilBox(unittest.TestCase):
    def setUp(self):
        Box().empty_my_stuff()

    def tearDown(self):
        Box().empty_my_stuff()

    def test_add_and_get(self):
        box = Box()
        box.add("k", "v")
        assert box.get("k") == "v"

    def test_get_missing_key_returns_none(self):
        box = Box()
        assert box.get("nope") is None

    def test_add_overwrites_existing_key(self):
        box = Box()
        box.add("k", "v1")
        box.add("k", "v2")
        assert box.get("k") == "v2"

    def test_remove(self):
        box = Box()
        box.add("k", "v")
        box.remove("k")
        assert box.get("k") is None

    def test_remove_missing_key_is_noop(self):
        box = Box()
        box.remove("nope")  # must not raise

    def test_get_my_stuff_returns_all_added_items(self):
        box = Box()
        box.add("a", 1)
        box.add("b", 2)
        stuff = box.get_my_stuff()
        assert stuff == {"a": 1, "b": 2}

    def test_get_my_stuff_is_empty_dict_when_nothing_added(self):
        box = Box()
        assert box.get_my_stuff() == {}

    def test_empty_my_stuff_clears_everything(self):
        box = Box()
        box.add("a", 1)
        box.add("b", 2)
        box.empty_my_stuff()
        assert box.get_my_stuff() == {}
        assert box.get("a") is None

    def test_empty_my_stuff_when_nothing_added_is_noop(self):
        box = Box()
        box.empty_my_stuff()  # must not raise

    def test_str_lists_current_thread_items(self):
        box = Box()
        box.add("a", 1)
        s = str(box)
        # __str__ is keyed by thread id, with each thread's whole dict as the value
        assert str(box._thread) in s
        assert "{'a': 1}" in s

    def test_known_constants_are_distinct_strings(self):
        keys = [
            Box.BOTO_S3_NOS,
            Box.BOTO_S3_CLIENT,
            Box.CSVPATHS_CONFIG,
            Box.SSH_CLIENT,
            Box.SFTP_CLIENT,
            Box.AZURE_BLOB_CLIENT,
            Box.GCS_STORAGE_CLIENT,
            Box.SQL_ENGINE,
        ]
        assert len(keys) == len(set(keys))

    def test_threads_do_not_share_stuff(self):
        box = Box()
        box.add("shared_key", "main_thread")

        other_thread_saw = {}

        def in_other_thread():
            other_box = Box()
            # a different thread's Box must not see this thread's value
            other_thread_saw["shared_key"] = other_box.get("shared_key")
            other_box.add("shared_key", "other_thread")
            other_thread_saw["own_value"] = other_box.get("shared_key")
            other_box.empty_my_stuff()

        t = threading.Thread(target=in_other_thread)
        t.start()
        t.join()

        assert other_thread_saw["shared_key"] is None
        assert other_thread_saw["own_value"] == "other_thread"
        # this thread's value must be unaffected by the other thread
        assert box.get("shared_key") == "main_thread"
