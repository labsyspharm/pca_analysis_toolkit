import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pcatk",
    version="0.1",
    author="Hung-Yi Wu",
    author_email="hungyi_wu@g.harvard.edu",
    description="Pre-Cancer Atlas data analysis toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hungyiwu/pca_analysis_toolkit",
    packages=setuptools.find_packages(),
    install_requires=[
        "numpy",
        "scikit-image",
        ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        ],
    )
