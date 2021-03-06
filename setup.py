from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

REQUIREMENTS = [
    'Click',
    'gitpython',
    'requests',
    'colorama',
]

CLASSIFIERS = [
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
]

setup(
    name='tradocs',
    version='1.5.1',
    author='Eber Rodrigues',
    author_email='eberjoe@gmail.com',
    description='DocFX localization',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/eberjoe/tradocs',
    license = 'MIT',
    packages = find_packages(),
    entry_points = {
        'console_scripts': ['tradocs = tradocs.tradocs:root']
    },
    classifiers = CLASSIFIERS,
    install_requires = REQUIREMENTS,
    python_requires='>=3.6',
)