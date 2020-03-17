import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="servicenow-api-client",
    version="0.0.8",
    author="Thiago Machado",
    author_email="thiagomachhado@gmail.com",
    description="A python client to Service Now API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        "Source Code": "https://github.com/thiagomachado/service_now_client"
    },
    install_requires=['requests'],
    packages=['servicenow_api_client'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
