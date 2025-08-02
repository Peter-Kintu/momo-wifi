import codecs
import os
import re

from setuptools import setup, find_packages

def read(*parts):
    """
    Reads a file from the project root.
    """
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as f:
        return f.read()

def find_version(*file_paths):
    """
    Reads the version from a file, matching the __version__ = '1.2.3' format.
    """
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# Core dependencies
install_requires = [
    'requests>=2.25.0',
    'urllib3>=1.26.0',
]

# Optional dependencies
docs_require = ['mkdocs']
tests_require = ['pytest>=2.8.0']
dev_requires = docs_require + tests_require

setup(
    name='mtnmomo',
    version=find_version('mtnmomo', '__init__.py'),
    url='https://github.com/Peter-Kintu/momo-wifi',
    license='MIT',
    author='Peter Kintu',
    author_email='kintupeter721@gmail.com',
    description='Custom fork of MTN MoMo Python SDK',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
        'docs': docs_require,
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    keywords='MTN MoMo mobile money API SDK Uganda payments',
    entry_points={
        'console_scripts': [
            # Uncomment and customize if you have CLI functionality
            # 'mtnmomo-cli=mtnmomo.cli:main',
        ],
    },
)