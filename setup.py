from setuptools import setup, find_packages

with open("README.rst") as fh:
    long_description = fh.read()

setup(
    name="chat_exporter",
    version="1.7.2",
    author="mahtoid",
    description="A simple Discord chat exporter for Python Discord bots.",
    long_description=long_description,
    url="https://github.com/mahtoid/DiscordChatExporterPy",
    packages=find_packages(),
    package_data={'': [r'chat_exporter/html/*.html']},
    include_package_data=True,
    license="GPL",
    install_requires=["aiohttp", "pytz", "grapheme", "emoji"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords="chat exporter",
)
