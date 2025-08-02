from setuptools import setup, find_packages

setup(
    name='mtnmomo',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.0',
        'urllib3>=1.26.0',
    ],
    author='Peter Kintu',
    description='Custom fork of MTN MoMo Python SDK',
    url='https://github.com/Peter-Kintu/momo-wifi',
)