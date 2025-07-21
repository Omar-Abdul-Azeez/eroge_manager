from setuptools import setup


setup(
    name='eroge_manager',
    version='1.0.0',
    packages=['eroge'],
    url='https://github.com/Omar-Abdul-Azeez/eroge_manager',
    install_requires=[
        'requests>=2.28',
        'regex>=2022.10.31',
        'beautifulsoup4>=4.11.1',
        'cfscrape>=2.1',
        'natsort>8.2.0'
    ],
    python_requires=">=3.9.0",
    author="Omar Abdul'Aziz",
    entry_points={
        "console_scripts": [
            "eroge=eroge.__main__:main",
        ]
    },
)
