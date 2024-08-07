"""Utilities for installing Python packages."""
from __future__ import annotations

import contextlib
import dataclasses
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import typing as t
import urllib.request


class Display:
    """Display interface for sending output to the console."""
    CLEAR = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'

    def section(self, message: str) -> None:
        """Print a section message to the console."""
        self.info(f'==> {message}', color=self.GREEN)

    def error(self, message: str) -> None:
        """Print an error message to the console."""
        self.info(message, color=self.RED)

    def info(self, message: str, color: t.Optional[str] = None) -> None:
        """Print a message to the console."""
        print(f'{color or self.CLEAR}{message}{self.CLEAR}', flush=True)


@dataclasses.dataclass(frozen=True)
class Python:
    """Details of a Python interpreter."""
    path: str
    version: str

    def show_version(self):
        """Show the Python version reported by the interpreter."""
        subprocess.run([self.path, '--version'], check=True)


class Pip:
    """Python interface for the pip CLI."""
    PIP_INDEX = 'https://d2c8fqinjk13kw.cloudfront.net/simple/'
    PIP_PROXY_VERSIONS: t.Tuple[str] = tuple()

    _OPTIONS = (
        '--disable-pip-version-check',
    )

    _DEFAULT_PACKAGES = dict(
        pip='24.2',
    )

    _PACKAGES: dict[str, dict[str, str]] = {
    }

    def __init__(self, python: Python) -> None:
        self.python = python
        self.packages = {name: version or self._DEFAULT_PACKAGES[name] for name, version in self._PACKAGES.get(python.version, self._DEFAULT_PACKAGES).items()}
        self.version = self.packages['pip']

        directory = os.path.dirname(os.path.abspath(__file__))

        self._pip_command = [python.path, '-B', os.path.join(directory, 'quiet_pip.py')]
        self._get_pip_path = f'/tmp/get_pip_{self.version.replace(".", "_")}.py'

    def have_get_pip(self) -> bool:
        """Return True if the get_pip installer has been downloaded, otherwise return False."""
        return os.path.exists(self._get_pip_path)

    def download_get_pip(self) -> None:
        """Download the get_pip installer."""
        with urllib.request.urlopen(f'https://ansible-ci-files.s3.amazonaws.com/ansible-test/get-pip-{self.version}.py') as download:
            with open(self._get_pip_path, 'wb') as file:
                shutil.copyfileobj(download, file)

    def setup(self):
        """Install pip using the get_pip installer."""
        env = os.environ.copy()
        env.update(GET_PIP=self._get_pip_path)

        packages = [f'{name}=={version}' for name, version in self.packages.items()]

        setup_options = [
            '--break-system-packages',
            '--no-setuptools',
            '--no-wheel',
        ]

        with self._install_options_context() as options:
            subprocess.run(self._pip_command + options + list(self._OPTIONS) + setup_options + packages, check=True, env=env)

    def show_version(self) -> None:
        """Show the pip version."""
        subprocess.run(self._pip_command + ['--version'] + list(self._OPTIONS), check=True)

    def wheel(self, args: t.List[str], constraints: pathlib.Path) -> None:
        """Build Python wheels with the given constraints file, storing them in the pip cache."""
        env = os.environ.copy()
        env.update(PIP_CONSTRAINT=str(constraints))

        with tempfile.TemporaryDirectory() as temp_dir:
            with self._install_options_context() as options:
                subprocess.run(self._pip_command + ['wheel'] + options + list(self._OPTIONS) + args, check=True, env=env, cwd=temp_dir)

    def install(self, args: t.List[str]) -> None:
        """Install Python packages."""
        with self._install_options_context() as options:
            subprocess.run(self._pip_command + ['install', '--break-system-packages'] + options + list(self._OPTIONS) + args, check=True)

    def list(self) -> t.List[t.Tuple[str, str]]:
        """Get a list of installed Python packages and versions."""
        result = subprocess.run(self._pip_command + ['list', '--format=json'] + list(self._OPTIONS), check=True, capture_output=True, text=True)
        items = json.loads(result.stdout)
        packages = [(item['name'], item['version']) for item in items]
        return packages

    def check(self) -> None:
        """Check installed Python packages."""
        subprocess.run(self._pip_command + ['check'] + list(self._OPTIONS), check=True)

    @staticmethod
    def purge_cache() -> None:
        """Purge the pip cache."""
        cache_dir = pathlib.Path('~/.cache/pip').expanduser()

        if cache_dir.exists():
            shutil.rmtree(cache_dir)  # The `pip cache purge` command leaves behind directories.

    @contextlib.contextmanager
    def _install_options_context(self) -> t.List[str]:
        """Create a pip install context for the specified Python interpreter and return options needed for the installation."""
        distutils_cfg_path = os.path.expanduser('~/.pydistutils.cfg')
        distutils_cfg = f'[easy_install]\nindex_url = {self.PIP_INDEX}'

        options = []

        if self.python.version in self.PIP_PROXY_VERSIONS:
            options.extend(['--index', self.PIP_INDEX])

            with open(distutils_cfg_path, 'w') as distutils_cfg_file:
                distutils_cfg_file.write(distutils_cfg)

        try:
            yield options
        finally:
            if self.python.version in self.PIP_PROXY_VERSIONS:
                os.unlink(distutils_cfg_path)


def str_to_version(version: str) -> t.Tuple[int, ...]:
    """Return a version tuple from a version string."""
    return tuple(int(n) for n in version.split('.'))


def get_default_python() -> Python:
    """Return the default Python interpreter."""
    version_script = 'import sys; print(".".join(str(v) for v in sys.version_info[:2]))'

    path = '/usr/bin/python'
    version = subprocess.run([path, '-c', version_script], check=True, capture_output=True, text=True).stdout.strip()

    python = Python(
        path=path,
        version=version,
    )

    return python


def get_pythons() -> t.List[Python]:
    """Return a list of the available Python interpreters."""
    directory = '/usr/bin'
    names = os.listdir(directory)
    matches = [re.search(r'^python(?P<version>[0-9]+\.[0-9]+)$', name) for name in names]
    pythons = sort_pythons([Python(path=os.path.join(directory, match.group(0)), version=match.group('version')) for match in matches if match])

    return pythons


def sort_pythons(pythons: t.List[Python], last: t.Optional[Python] = None) -> t.List[Python]:
    """Return a sorted list of the given Python interpreters, putting the last interpreter at the end of the list (if given)."""
    if last:
        pythons = sorted(pythons, key=lambda item: tuple([100]) if item.version == last.version else str_to_version(item.version))
    else:
        pythons = sorted(pythons, key=lambda item: str_to_version(item.version))

    return pythons


def iterate_pythons() -> t.Iterator[Python]:
    """Iterate through the available Python interpreters."""
    display.section(f'Finding Python interpreters')

    default_python = get_default_python()

    pythons = get_pythons()

    for python in pythons:
        display.info(f'{python.version}{" (default)" if python.version == default_python.version else ""}')

    display.section(f'Setting up Python interpreters')

    yield from sort_pythons(pythons, default_python)


display = Display()
