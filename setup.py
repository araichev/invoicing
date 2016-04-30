from distutils.core import setup

dependencies = [
    'pandas>=0.18',
    'Jinja2>=2.8',
    ]
setup(
    name='invoicing',
    version='3.0.0',
    author='Alex Raichev',
    author_email='alex@raichev.net',
    packages=['invoicing', 'tests'],
    url='https://github.com/araichev/invoicing',
    license='LICENSE',
    description='A Python 3.4+ program for creating invoices from CSV timesheets',
    long_description=open('README.rst').read(),
    install_requires=dependencies,
    )

