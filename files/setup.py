"""Find installed Python interpreters and install pip in each one."""
from __future__ import annotations

import pathlib

from installer import (
    Pip,
    Python,
    display,
    iterate_pythons,
)


def main() -> None:
    """Main entry point."""
    tmp = pathlib.Path('/tmp')

    if unexpected := list(tmp.iterdir()):
        raise Exception(f'Unexpected temporary files: {unexpected}')

    for python in iterate_pythons():
        setup_python(python)

    for path in tmp.iterdir():
        display.info(f'Removing temporary file: {path}')
        path.unlink()


def setup_python(python: Python) -> None:
    """Setup the specified Python interpreter."""
    display.section(f'Started setup of Python {python.version}')
    display.info(python.path)

    display.section(f'Checking full Python version for Python {python.version}')
    python.show_version()

    pip = Pip(python)

    if not pip.have_get_pip():
        display.section(f'Downloading pip {pip.version}')
        pip.download_get_pip()

    display.section(f'Installing pip {pip.version} for Python {python.version}')
    pip.setup()

    display.section(f'Checking full pip version for Python {python.version}')
    pip.show_version()

    display.section(f'Checking pip integrity for Python {python.version}')
    pip.check()

    display.section(f'Listing installed packages for Python {python.version}')

    for name, version in pip.list():
        display.info(f'{name} {version}')

    display.section(f'Completed setup of Python {python.version}')


if __name__ == '__main__':
    main()
