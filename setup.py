from setuptools import setup

setup(
    name='timetracker',
    version='0.0.1',
    url='https://github.com/sasha0/timetracker',
    author="Alexander Gaevsky",
    packages=['timetracker'],
    include_package_data=True,
    install_requires=[
        'SQLAlchemy==1.0.12'
    ],
)
