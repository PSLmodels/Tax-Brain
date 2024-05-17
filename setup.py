import setuptools

install_requires = ["taxcalc", "behresp", "dask", "bokeh"]

with open("README.md", "r") as f:
    long_description = f.read()
version = "2.7.0"
setuptools.setup(
    name="taxbrain",
    version=version,
    author="Anderson Frailey",
    author_email="andersonfrailey@gmail.com",
    description="Python library for advanced tax policy analysis",
    long_description=long_description,
    url="https://github.com/PSLmodels/Tax-Brain",
    packages=["taxbrain"],
    install_requires=install_requires,
    tests_require=["pytest", "compdevkit"],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    entry_points={"console_scripts": ["taxbrain = taxbrain.cli:cli_main"]},
)
