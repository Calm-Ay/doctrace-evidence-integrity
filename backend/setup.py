from setuptools import setup, find_packages
setup(
    name="doctrace",
    version="0.1.0",
    packages=find_packages(include=["doctrace", "doctrace.*"]),
    install_requires=[
        "click>=8.0.0",
        "pymupdf>=1.22.0",
        "pikepdf>=8.0.0",
        "opencv-python>=4.7.0",
        "pytesseract>=0.3.10",
        "rich>=12.0.0",
        "pillow>=9.0.0",
        "numpy>=1.22.0"
    ],
    entry_points={
        "console_scripts": [
            "doctrace=doctrace.cli:cli"
        ]
    }
)
