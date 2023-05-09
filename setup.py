from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import setup
from setuptools import find_packages


def _requires_from_file(filename):
    return open(filename).read().splitlines()


setup(
    name="django_multi_forms_view",
    version="1.3.1",
    license="ライセンス",
    description="djangoのカスタムView",
    author="jarunga",
    url="https://github.com/Jarunga/django_multi_forms_view.git",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=["django_multi_forms_view.views.generic."+splitext(basename(path))[0] for path in glob('src/**/*.py',recursive=True)],
    include_package_data=True,
    zip_safe=False,
    install_requires=_requires_from_file('requirements.txt'),
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-cov"]
)
