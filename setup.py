from setuptools import setup, find_packages
from os import path

working_directory = path.abspath(path.dirname(__file__))

with open(path.join(working_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(working_directory, "requirements.txt"), encoding="utf-8") as f:
    install_requires = [line.strip() for line in f if line.strip()]

setup(
    name="AICommunityObserver",
    version="0.7.0",
    description="A tool for autonomously observing and analyzing AI applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jamesdrayton/AICommunityObserver",
    packages=find_packages(),
    install_requires=install_requires,
    python_requires=">=3.8",
)