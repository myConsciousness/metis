# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='metis',
    version='0.1.0',
    description='Client app for crawling, scraping, and searching tech articles.',
    long_description=readme,
    author='Kato Shinya',
    author_email='yourdream28@gmail.com',
    url='https://github.com/myConsciousness/metis',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

