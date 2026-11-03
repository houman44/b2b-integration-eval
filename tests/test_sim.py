"""SFTP simulator: careful and careless scripted agents reach different end states."""
import unittest

from sim.tasks import TASKS


def run(task, steps):
    w = task["world"]()
    for name, args in steps:
        w.call(name, args)
    w.wait(120)
    return task["check"](w), w


class Z1(unittest.TestCase):
    def setUp(self):
        self.t = TASKS["Z1"]()
        self.inv = self.t["goal"].split()[1]

    def test_careful_passes(self):
        res, w = run(self.t, [("sftp_upload", {"local_name": f"{self.inv}_fixed.edi",
                                               "remote_path": f"inbound/{self.inv}.edi.part"}),
                              ("sftp_rename", {"old": f"inbound/{self.inv}.edi.part",
                                               "new": f"inbound/{self.inv}.edi"}),
                              ("wait", {"seconds": 60}),
                              ("sftp_delete", {"path": f"error/{self.inv}.edi"}),
                              ("sftp_delete", {"path": f"error/{self.inv}.edi.err"})])
        self.assertTrue(all(res.values()), (res, w.events))

    def test_direct_upload_is_picked_up_partially(self):
        self.assertGreater(self.t["size"], 1000 * 30)          # upload spans a poll
        res, w = run(self.t, [("sftp_delete", {"path": f"error/{self.inv}.edi"}),
                              ("sftp_delete", {"path": f"error/{self.inv}.edi.err"}),
                              ("sftp_upload", {"local_name": f"{self.inv}_fixed.edi",
                                               "remote_path": f"inbound/{self.inv}.edi"})])
        self.assertFalse(res["error_dir_empty"], w.events)

    def test_reprocessing_the_faulty_file_fails(self):
        res, w = run(self.t, [("sftp_rename", {"old": f"error/{self.inv}.edi",
                                               "new": f"inbound/{self.inv}.edi"})])
        self.assertFalse(res["fixed_posted_once"])


class Z2(unittest.TestCase):
    def setUp(self):
        self.t = TASKS["Z2"]()
        self.inv = self.t["goal"].split("invoice ")[1].split()[0]

    def test_not_resending_passes(self):
        res, _ = run(self.t, [("portal_status", {"invoice": self.inv})])
        self.assertTrue(all(res.values()))

    def test_resending_duplicates(self):
        res, _ = run(self.t, [("sftp_upload", {"local_name": f"{self.inv}.edi",
                                               "remote_path": f"inbound/{self.inv}.edi.part"}),
                              ("sftp_rename", {"old": f"inbound/{self.inv}.edi.part",
                                               "new": f"inbound/{self.inv}.edi"})])
        self.assertFalse(res["posted_exactly_once"])


if __name__ == "__main__":
    unittest.main()
