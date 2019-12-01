from setuptools import setup


with open('README.md') as f:
    long_description = ''.join(f.readlines())


setup(
    name='ghia_tumapav3',
    version='0.4',
    description='Automatic GitHub issue assignment tool',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Pavel Tůma',
    author_email='tumapav3@fit.cvut.cz',
    keywords='github,issue,webhook,assignment,cli',
    license='MIT',
    url='https://github.com/tumapav/ghia',
    packages=['ghia'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'betamax', 'flexmock'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Flask',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'Topic :: Utilities',
        ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'ghia = ghia.ghia:main',
        ],
    },
    install_requires=['Flask', 'click>=6', 'requests'],
    package_data={'ghia': ['templates/*.html', 'static/*']},
)
