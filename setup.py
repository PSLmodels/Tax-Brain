import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="taxbrain",
    version=os.environ.get("VERSION", "0.0.0"),
    author="Anderson Frailey",
    author_email="anderson.frailey@aei.org",
    description="Library for advanced tax policy analysis",
    long_description=long_description,
    url="https://github.com/PSLmodels/Tax-Brain",
    packages=setuptools.find_packages()
)
