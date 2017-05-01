from setuptools import setup

version = '0.1.0'

setup(
    name='sharemux',
    version=version,
    description='Share your tmux session via a hosted web page',
    long_description='Share your tmux session via a hosted web page',
    url='https://github.com/doylezdead/sharemux',
    download_url='https://github.com/doylezdead/sharemux/tarball/{}'.format(version),
    author='Ryan Doyle',
    author_email='rcdoyle@mtu.edu',
    license='MIT',
    packages=['sharemux'],
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
    keywords='tmux share host broadcast',
    entry_points={
        'console_scripts': [
            'sharemux = sharemux:cli'
        ]
    },
    install_requires=[
        'click',
        'pexpect',
        'Flask'
    ],
    include_package_data=True,
    zip_safe=False
)
