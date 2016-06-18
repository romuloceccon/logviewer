import configparser
import os.path

class Configuration(object):
    class Error(Exception):
        pass

    def __init__(self, filename, driver_map):
        self._timeout = None
        self._driver_map = driver_map
        self._driver = None
        self._driver_args = {}
        self._load_file(filename)

    def _load_file(self, filename):
        config = configparser.ConfigParser()

        try:
            with open(filename) as f:
                config.read_string(f.read())
        except IOError:
            raise Configuration.Error("Cannot read config file `{}`".
                format(filename))

        main = config['main']
        if 'timeout' in main:
            self._timeout = float(main['timeout'])
        if 'backend' in main:
            backend = main['backend']
            if not backend in self._driver_map:
                raise Configuration.Error("Invalid backend `{}`. Maybe some "\
                    "dependency is missing?".format(backend))
            self._driver = self._driver_map[backend]
            self._driver_args = config[backend]

    @property
    def timeout(self):
        return self._timeout

    def get_factory(self):
        if not self._driver:
            raise Configuration.Error("No backend configured")
        return self._driver(**(self._driver_args))
