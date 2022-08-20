# Resources:
# - https://caremad.io/posts/2013/07/setup-vs-requirement/
# - https://stackoverflow.com/questions/14399534/reference-requirements-txt-for-the-install-requires-kwarg-in-setuptools-setup-py/16624700#16624700

from setuptools import find_packages, setup

setup(
    name='cryptowatson-indicators',
    packages=find_packages(include=['cryptowatson_indicators*']),
    version='0.0.2',
    description='Python package to calculate crypto indicators and run trading simulations',
    author='Me',
    license='MIT',
    install_requires=[
        'python-dotenv',
        'requests',
        'numpy',
        'pandas',
        'scipy',
        'Nasdaq-Data-Link',
        'python-binance',
        'matplotlib',
        'matplotlib-inline',
        'backtrader',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)
