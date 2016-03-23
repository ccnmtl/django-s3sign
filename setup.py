import os
from setuptools import setup

ROOT = os.path.abspath(os.path.dirname(__file__))

setup(
    name="django-s3sign",
    version="0.1.1",
    author="Anders Pearson",
    author_email="anders@columbia.edu",
    url="https://github.com/ccnmtl/django-s3sign",
    description="Django smoketest framework",
    long_description=open(os.path.join(ROOT, 'README.md')).read(),
    install_requires=['Django>=1.8', 'nose'],
    scripts=[],
    license="GPL3",
    platforms=["any"],
    zip_safe=False,
    package_data = {'': ['*.*']},
    packages=['s3sign'],
    test_suite='nose.collector',
    include_package_data=True,
)
