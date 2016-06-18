import unittest

import tempfile
import os.path

from configuration import Configuration
import sqlite3_driver

class ConfigurationTest(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._conf_file = os.path.join(self._temp_dir.name, 'conf.conf')

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_should_get_timeout(self):
        with open(self._conf_file, 'w+') as f:
            f.write('''[main]
timeout = 2
''')
        config = Configuration(self._conf_file, {})
        self.assertEqual(2, config.timeout)

    def test_should_get_driver_factory(self):
        with open(self._conf_file, 'w+') as f:
            f.write('''[main]
backend = sqlite3

[sqlite3]
filename = test.db
''')
        config = Configuration(self._conf_file,
            { 'sqlite3': sqlite3_driver.Sqlite3Driver.Factory })
        factory = config.get_factory()
        self.assertIsInstance(factory, sqlite3_driver.Sqlite3Driver.Factory)
        self.assertEqual('test.db', factory._filename)

    def test_should_handle_default_config(self):
        with open(self._conf_file, 'w+') as f:
            f.write('[main]\n')

        config = Configuration(self._conf_file, {})
        self.assertIsNone(config.timeout)
        self.assertRaises(Configuration.Error, config.get_factory)

    def test_should_fail_if_file_is_missing(self):
        self.assertRaises(Configuration.Error,
            Configuration, self._conf_file, {})

    def test_should_validate_backend(self):
        with open(self._conf_file, 'w+') as f:
            f.write('''[main]
backend = oracle

[oracle]
database = test
''')
        self.assertRaises(Configuration.Error,
            Configuration, self._conf_file, {})
