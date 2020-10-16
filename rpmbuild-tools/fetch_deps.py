#!/opt/rh/rh-python36/root/bin/python3
import subprocess
import os
import shutil
from collections import deque

import re
import requests
import requirements
from pip._internal.index.collector import LinkCollector
from pip._internal.index.package_finder import PackageFinder
from pip._internal.models.format_control import FormatControl
from pip._internal.models.search_scope import SearchScope
from pip._internal.models.target_python import TargetPython
from pip._internal.network.session import PipSession
from pip._vendor.packaging.specifiers import SpecifierSet

pypi_session = requests.sessions.Session()

def get_best_package(package_name, specifier=''):
    allow_yanked = True
    ignore_requires_python = True
    target_python = TargetPython(py_version_info=(3, 8, 3))
    format_control = FormatControl({':all:'}, {})
    link_collector = LinkCollector(
        session=PipSession(),
        search_scope=SearchScope([], ['https://pypi.org/simple']),
    )
    finder = PackageFinder(
        link_collector=link_collector,
        target_python=target_python,
        allow_yanked=allow_yanked,
        format_control=format_control,
        ignore_requires_python=ignore_requires_python,
    )
    cand = finder.find_best_candidate(package_name, SpecifierSet(specifier))
    return cand.best_candidate.name, cand.best_candidate.version, cand.best_candidate.link.url

def download_best_package(package_name, specifier=''):
    name, version, url = get_best_package(package_name, specifier)
    url_split = url.split('#sha256')[0]
    file_split = url_split.split('/')[-1]
    dest = str(name)+ "/" +str(file_split)
    r = requests.get(url_split, allow_redirects=True)
    open(dest, 'wb').write(r.content)
    unpack_files(dest)

def unpack_files(dest):
    dest_dir = dest.split('/')[0]
    shutil.unpack_archive(dest, dest_dir)

def get_package_info(package):
    url = 'https://pypi.python.org/pypi/' + package + '/json'
    response = pypi_session.get(url, allow_redirects=True)
    try:
        data = response.json()
    except:  # Something went wrong when parsing the response as JSON, print some useful information
        print(package)
        print(response.text)
        raise
    return data
    print(data)

"""
Try to get a sane version from a list of specs or just return False 
"""

def version_from_specs(specs):
    version = specs[0][1] if len(specs) > 0 and specs[0][0] == "==" else False

    if (version):  # Clean version
        # foo == 1.4.*
        if ("*" in version):
            version = False

    return version

"""
Returns a list of dependencies for a package
"""

def get_dependencies_of(package):
    data = get_package_info(package.name)
    if not os.path.exists(package.name):
        os.makedirs(package.name)
    download_best_package(package.name, ''.join(package.specs[0]) if package.specs else '')
    dependencies = data['info']['requires_dist']

    # Return a list of requirements
    to_return = []
    if (isinstance(dependencies, list)):
        for d in dependencies:
            parsed = requirements.requirement.Requirement.parse(d)
            if 'extra' in parsed.line:
                continue

            if 'python_version' in parsed.line and 3.6 >= float(re.split('\'|"', parsed.line.split('python_version')[1])[1]):
                continue

            to_return.append(parsed)
    return to_return

if __name__ == "__main__":
    work_queue = deque()    # Queue of packages to get dependencies of
    known_packages = set()  # Packages we all-ready know

    # Fetch latest reqiurements.txt from official awx repo
    subprocess.check_call(['curl', '-s', '-O', 'https://raw.githubusercontent.com/ansible/awx/devel/requirements/requirements.txt'], stdout=open(os.devnull, 'wb'))
    
    # Populate queue with initial list of packages
    with open("requirements.txt") as fp:
        for req in requirements.parse(fp):
            work_queue.append(req)
            known_packages.add(req.name)

    # Work through queue until we have checked everything
    while True:
        try:
            req = work_queue.popleft()  # Get first in queue
        except IndexError:
            print("=== Done, work queue is empty. Known packages: {0}".format(len(known_packages)))
            break

        dependencies = get_dependencies_of(req)

        print(f'{req.name}{req.specs[0][0]}{req.specs[0][1]}' if req.specs else f'{req.name}')
        for dependency in dependencies:
            print(f'\t{dependency.name}{dependency.specs[0][0]}{dependency.specs[0][1]}' if dependency.specs else f'\t{dependency.name}')

            # Only add new dependencies to queue
            if not dependency.name in known_packages:
                work_queue.append(dependency)
                known_packages.add(dependency.name)
