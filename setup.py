from setuptools import setup, find_packages

setup(
    name="pytestflow",
    version="0.2.0",
    description="Test automation framework inspired by NI TestStand, built on Prefect",
    author="Alberto Manzoni",
    author_email="alb.manzoni@gmail.com",
    url="https://github.com/Alberto-Manzoni/PyTestFlow",
    packages=find_packages(),
    include_package_data=True,  # fondamentale!
    install_requires=[
        "prefect==3.6.24",
        "pandas",
        "numpy",
        "rich",
        "bottle",
        "websockets",
    ],
    entry_points={
        "console_scripts": [
            "pytestflow=pytestflow.cli:main",
        ]
    },
    python_requires=">=3.11",
)