from setuptools import setup, find_packages


long_description = open('README.md', 'r', encoding='utf-8').read()

setup(
    name="camptools",
    version="0.3.0",
    install_requires=[
        'f90nml',
    ],
    entry_points={
        'console_scripts': [
            'nmyqsub = camptools.qsub_wrapper:nmyqsub',
            'myqsub = camptools.qsub_wrapper:myqsub',
            'job_status = camptools.job_status:job_status',
            'joblist = camptools.job_status:joblist',
            'jobhistory = camptools.job_history:job_history',
            'mymkdir = camptools.mymkdir:mymkdir',
        ]
    },
    author="Nkzono",
    author_email="71783375+Nkzono99@users.noreply.github.com",
    description="Tools for camphor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nkzono99/camptools",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)