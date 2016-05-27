import unittest
import random

from sql_driver import SqlDriver

class SqlDriverTest(unittest.TestCase):
    class FakeSqlDriver(SqlDriver):
        def __init__(self, level=None):
            SqlDriver.__init__(self, level)
            self.query = None
            self.magic = random.randint(1, 1000)

        def select(self, query):
            self.query = query
            return self.magic

    def test_should_execute_query_without_initial_id(self):
        drv = SqlDriverTest.FakeSqlDriver()
        self.assertEqual(drv.magic, drv.prepare_query(None, True, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_execute_query_with_different_limit(self):
        drv = SqlDriverTest.FakeSqlDriver()
        self.assertEqual(drv.magic, drv.prepare_query(None, True, 1))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs ORDER BY id DESC LIMIT 1", drv.query)

    def test_should_execute_query_with_an_initial_id(self):
        drv = SqlDriverTest.FakeSqlDriver()
        self.assertEqual(drv.magic, drv.prepare_query(100, True, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 ORDER BY id DESC LIMIT 10",
            drv.query)

    def test_should_execute_query_in_ascending_order(self):
        drv = SqlDriverTest.FakeSqlDriver()
        self.assertEqual(drv.magic, drv.prepare_query(100, False, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id > 100 ORDER BY id ASC LIMIT 10",
            drv.query)

    def test_should_execute_query_with_level_filter(self):
        drv = SqlDriverTest.FakeSqlDriver(level=3)
        self.assertEqual(drv.magic, drv.prepare_query(100, True, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND level_num <= 3 "\
            "ORDER BY id DESC LIMIT 10", drv.query)
