from setuptools import setup, find_packages

setup(
    name="iskra",
    version="0.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)