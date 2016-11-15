from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='logviewer',
    version='0.1',
    description='A curses-bases syslog viewer',
    long_description=readme(),
    url='https://github.com/romuloceccon/logviewer',
    author='Rômulo A. Ceccon',
    author_email='romuloceccon@gmail.com',
    license='MIT',
    packages=['logviewer'],
    scripts=['bin/logviewer'],
    zip_safe=False)
