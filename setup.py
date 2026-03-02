from setuptools import setup, find_packages

setup(
    name="presentation-framework",
    version="0.2.0",
    description="Generate branded HTML slide decks from YAML + JSON",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "pf": ["schema.json"],
    },
    install_requires=[
        "jinja2>=3.0",
        "pyyaml>=6.0",
        "click>=8.0",
        "watchdog>=3.0",
        "jsonschema>=4.0",
    ],
    extras_require={
        "pdf": ["playwright>=1.40"],
    },
    entry_points={
        "console_scripts": [
            "pf=pf.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
