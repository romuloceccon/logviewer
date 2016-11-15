import unittest
import random
import datetime

from sql_driver import SQLDriver

class SQLDriverTest(unittest.TestCase):
    class FakeSQLDriver(SQLDriver):
        def __init__(self, **kwargs):
            SQLDriver.__init__(self, **kwargs)
            self.query = None
            self.magic = random.randint(1, 1000)

        def select(self, query):
            self.query = query
            return self.magic

    def test_should_execute_query_without_initial_id(self):
        drv = SQLDriverTest.FakeSQLDriver()
        self.assertEqual(drv.magic, drv.prepare_query(None, True, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_execute_query_with_different_limit(self):
        drv = SQLDriverTest.FakeSQLDriver()
        self.assertEqual(drv.magic, drv.prepare_query(None, True, 1))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs ORDER BY id DESC LIMIT 1", drv.query)

    def test_should_execute_query_with_an_initial_id(self):
        drv = SQLDriverTest.FakeSQLDriver()
        self.assertEqual(drv.magic, drv.prepare_query(100, True, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 ORDER BY id DESC LIMIT 10",
            drv.query)

    def test_should_execute_query_in_ascending_order(self):
        drv = SQLDriverTest.FakeSQLDriver()
        self.assertEqual(drv.magic, drv.prepare_query(100, False, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id > 100 ORDER BY id ASC LIMIT 10",
            drv.query)

    def test_should_execute_query_with_level_filter(self):
        drv = SQLDriverTest.FakeSQLDriver(level=3)
        self.assertEqual(drv.magic, drv.prepare_query(100, True, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND level_num <= 3 "\
            "ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_execute_query_with_facility_filter(self):
        drv = SQLDriverTest.FakeSQLDriver(facility=5)
        self.assertEqual(drv.magic, drv.prepare_query(100, True, 10))

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND facility_num = 5 "\
            "ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_filter_query_by_one_program(self):
        drv = SQLDriverTest.FakeSQLDriver(program='sshd')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "(program = 'sshd') ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_filter_query_by_multiple_programs(self):
        drv = SQLDriverTest.FakeSQLDriver(program='sshd sudo')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "(program = 'sshd' OR program = 'sudo') ORDER BY id DESC LIMIT 10",
            drv.query)

    def test_should_filter_by_program_stripping_extra_spaces(self):
        drv = SQLDriverTest.FakeSQLDriver(program=' sshd  sudo ')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "(program = 'sshd' OR program = 'sudo') ORDER BY id DESC LIMIT 10",
            drv.query)

    def test_should_filter_program_with_wildcard(self):
        drv = SQLDriverTest.FakeSQLDriver(program='s*')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "(program LIKE 's%') ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_filter_program_with_negative_condition(self):
        drv = SQLDriverTest.FakeSQLDriver(program='!sshd')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "program <> 'sshd' ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_filter_program_with_negative_wildcard_condition(self):
        drv = SQLDriverTest.FakeSQLDriver(program='!s*')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "program NOT LIKE 's%' ORDER BY id DESC LIMIT 10", drv.query)

    def test_should_filter_program_with_multiple_negative_conditions(self):
        drv = SQLDriverTest.FakeSQLDriver(program='!sshd !sudo')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "program <> 'sshd' AND program <> 'sudo' ORDER BY id DESC LIMIT 10",
            drv.query)

    def test_should_filter_program_with_positive_and_negative_conditions(self):
        drv = SQLDriverTest.FakeSQLDriver(program='!sshd s*')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "(program LIKE 's%') AND program <> 'sshd' ORDER BY id DESC LIMIT 10",
            drv.query)

    def test_should_filter_host_with_multiple_conditions(self):
        drv = SQLDriverTest.FakeSQLDriver(host='h1 h2')
        drv.prepare_query(100, True, 10)

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE id < 100 AND "\
            "(host = 'h1' OR host = 'h2') ORDER BY id DESC LIMIT 10",
            drv.query)

    def test_should_find_date(self):
        drv = SQLDriverTest.FakeSQLDriver(
            start_date=datetime.datetime(2016, 6, 27, 22, 27, 50))
        drv.prepare_datetime_query()

        self.assertEqual("SELECT id, facility_num, level_num, host, datetime, "\
            "program, pid, message FROM logs WHERE datetime >= "\
            "'2016-06-27 22:27:50' ORDER BY datetime ASC LIMIT 1", drv.query)
