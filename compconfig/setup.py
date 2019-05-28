# setup.py helps py.test find your tests in comp/tests/test_functions.py
import setuptools

setuptools.setup(
    name="compconfig",
    description="COMP configuration for Tax-Brain",
    packages=setuptools.find_packages(),
    include_package_data=True
)
