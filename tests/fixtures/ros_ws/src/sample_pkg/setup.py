"""Setup of the sample_pkg package."""

from setuptools import find_packages, setup

PACKAGE_NAME = "sample_pkg"

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{PACKAGE_NAME}"]),
        (f"share/{PACKAGE_NAME}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="CATIE",
    maintainer_email="sonu@catie.fr",
    description="Sample ament_python package used by the ros_workflows self-test.",
    license="Apache-2.0",
    entry_points={"console_scripts": ["talker = sample_pkg.talker:main"]},
)
