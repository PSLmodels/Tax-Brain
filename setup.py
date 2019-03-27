import setuptools

with open("README.md", "r") as f:
    long_description = f.read()
version = "0.0.0"
setuptools.setup(
    name="taxbrain",
    version=version,
    author="Anderson Frailey",
    author_email="anderson.frailey@aei.org",
    description="Python library for advanced tax policy analysis",
    long_description=long_description,
    url="https://github.com/PSLmodels/Tax-Brain",
    packages=["taxbrain", "taxbrain.tbi"],
    install_requires=["taxcalc", "behresp", "dask", "bokeh"],
    tests_require=["pytest"],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Opperating Sytem :: OS Independent"
    ],
    include_package_data=True
)
