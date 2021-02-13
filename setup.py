from setuptools import setup

kwargs = {
        'packages': ['ledger-common'],
        'include_package_data': True,
        'install_requires': [
            'django>=1.8,<=1.11.29',
            ],
        'test_suite': 'test_suite',
        'name': 'ledger-common',
        #'version': __import__('preserialize').get_version(),
        'author': 'Brendan Blackford',
        'author_email': 'brendan.blackford@dbca.wa.gov.au',
        'description': 'Shared library for Ledger applications',
        'license': 'BSD',
        #'keywords': 'serialize model queryset django',
        #'url': 'https://github.com/bruth/django-preserialize/',
        'classifiers': [
            #'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            ],
        }

setup(**kwargs)
