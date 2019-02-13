from setuptools import setup

version = '0.3.0'

setup(
    name='sharemux',
    version=version,
    description='Share your tmux session via a hosted web page',
    long_description='Share your tmux session via a hosted web page',
    url='https://gitlab.com/rdoyle/sharemux',
    download_url='https://gitlab.com/rdoyle/sharemux/-/archive/master/sharemux-master.tar.gz',
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
            'sharemux = sharemux.webserver:cli_websrv_start'
        ]
    },
    install_requires=[
        'click==7.0',
        'pexpect==4.6.0',
        'Flask==1.0.2'
    ],
    include_package_data=True,
    zip_safe=False
)
