import json
import re
import shutil
from collections import deque

import requests
import requirements
from pip._internal.index.collector import LinkCollector
from pip._internal.index.package_finder import PackageFinder
from pip._internal.models.format_control import FormatControl
from pip._internal.models.search_scope import SearchScope
from pip._internal.models.target_python import TargetPython
from pip._internal.network.session import PipSession
from pip._vendor.packaging.specifiers import SpecifierSet

SOURCE_URL = 'https://raw.githubusercontent.com/ansible/awx/devel/requirements/requirements.txt'

pypi_session = requests.sessions.Session()


def unpack_files(dest):
    dest_dir = dest.split('/')[0]
    shutil.unpack_archive(dest, dest_dir)


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
    dest = str(name) + "/" + str(file_split)
    r = requests.get(url_split, allow_redirects=True)
    open(dest, 'wb').write(r.content)
    unpack_files(dest)


def get_package_info(package):
    url = 'https://pypi.python.org/pypi/' + package + '/json'
    response = pypi_session.get(url, allow_redirects=True)
    data = response.json()
    return data


# fetch requirements.txt
def fetch_all_from_source():
    resp = requests.get(SOURCE_URL)
    pkgs = resp.text

    packages = []
    for pkg in requirements.parse(pkgs):
        packages.append({
            'name': pkg.name,
            'specifier': pkg.specs[0][0] if pkg.specs else '',
            'version': pkg.specs[0][1] if pkg.specs else ''
        })

    return packages


def fetch_pkg_dependencies(pkg_name):
    fetched = get_package_info(pkg_name)  # fetch from pypi
    dependencies = fetched['info']['requires_dist']
    to_return = []
    if dependencies:
        for d in dependencies:
            parsed = requirements.requirement.Requirement.parse(d)
            if 'extra' in parsed.line:
                continue
            if 'python_version' in parsed.line and 3.6 >= float(
                    re.split('\'|"', parsed.line.split('python_version')[1])[1]):
                continue
            spec, ver = parsed.specs[0] if parsed.specs else ('', '')
            to_return.append({'name': parsed.name, 'version': ver, 'specifier': spec})
            # res = fetch_pkg_dependencies(parsed.name, spec, ver, outer=False)
            # for r in res:
            #     to_return.append(r)

    return to_return


def fetch_all_inc_deps(all_packages):
    work_queue = deque()
    known_packages = set()  # Packages we all-ready know
    for pkg in all_packages:
        work_queue.append(pkg)
        known_packages.add(pkg['name'])

    fetched_list = []
    while work_queue:
        pkg = work_queue.popleft()
        deps = fetch_pkg_dependencies(pkg['name'])
        print(f"Fetching {pkg['name']}")
        fetched_list.append({
            **pkg,
            'dependencies': deps
        })

        for dep in deps:
            if dep['name'] not in known_packages:
                work_queue.append(dep)
                known_packages.add(dep['name'])

    return fetched_list


def _condense_dependencies(fetched_list, facit):
    packages = {}
    for pkg in facit:  # add known packages with definite versions to dict
        packages[pkg['name']] = {'name': pkg['name'], 'definite_version': pkg['version'], 'required_by': {}}

    for pkg in fetched_list:
        if pkg['name'] not in packages:  # most likely a dependency if it is not in the list
            packages[pkg['name']] = {'name': pkg['name'], 'dependencies': pkg['dependencies'], 'required_by': {}}
        else:  # otherwise add the dependencies to the existing package in the dict
            packages[pkg['name']]['dependencies'] = pkg['dependencies']

        for dep in pkg['dependencies']:
            dep_name = dep['name']

            if dep_name not in packages:
                # notice, this is what the package WANTS of the dependency
                packages[dep_name] = {'name': dep_name, 'required_by': {pkg['name']: dep['specifier'] + dep['version']}}
            else:
                # notice, this is what the package WANTS of the dependency
                packages[dep_name]['required_by'][pkg['name']] = dep['specifier'] + dep['version']

    return packages


def _set_definite_versions(condensed):
    for pkg_name in condensed:
        package = condensed[pkg_name]
        if 'definite_version' in package:
            continue

        specifier = ''
        for ver in package['required_by'].values():
            specifier += ver + ','
        best_pkg = get_best_package(pkg_name, specifier)
        condensed[pkg_name]['definite_version'] = best_pkg[1].base_version


def fetch_all_requirements_reqs():
    all_packages = fetch_all_from_source()
    fetched_all = fetch_all_inc_deps(all_packages)
    condensed = _condense_dependencies(fetched_all, all_packages)
    _set_definite_versions(condensed)
    return condensed


if __name__ == '__main__':
    res = fetch_all_requirements_reqs()

    with open('fetched_all.json', 'w') as fp:
        json.dump(res, fp, indent=4)

    # facit = fetch_all_from_source()
    # with open('fetched_all.json', 'r') as fp:
    #     loaded = fp.read()
    #     fetched_list = json.loads(loaded.lower())
    #     condensed = _condense_dependencies(fetched_list, facit)
    #     set_definite_versions(condensed)
    #     with open('out.json', 'w') as out:
    #         json.dump(condensed, out, indent=4)
