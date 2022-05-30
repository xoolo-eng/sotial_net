import pathlib
from setuptools import setup, find_packages

BASE_DIR = pathlib.Path(__file__).parent.absolute()


def get_version():
    with open(BASE_DIR / "VERSION") as file:
        return file.readline().strip()


def get_license():
    with open(BASE_DIR / "LICENSE") as file:
        return file.read().strip()


def get_description():
    with open(BASE_DIR / "README.md") as file:
        return file.read().strip()


def get_packages():
    with open(BASE_DIR / "requirements.txt") as file:
        return [package.strip() for package in file.readlines()]


setup(
    name="snet",
    version=get_version(),
    author="Dzmitry Amelchanka",
    author_email="dima.amelchenko@live.com",
    url="",
    license=get_license(),
    packages=find_packages(".", include=["snet"]),
    package_dir={"": "."},
    include_package_data=True,
    description="Sotial network.",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    install_requires=get_packages(),
    python_require=">=3.9",
    zip_sefe=True,
    entry_points={"console_scripts": ["s_net = snet.app:run"]},
    classifiers=[
        "Development Status :: 3 - Alpha"
        if "dev" in get_version()
        else "Development Status :: 4 Beta"
        if "rc" in get_version()
        else "Development Status :: 5 Production/Stable"
    ],
)
