
import argparse
import glob
import json
import subprocess

PREFIX = 'awx-python36'
PACKAGER = 'Sinan Sert <sis@miracle.dk>'


parser = argparse.ArgumentParser(description='Generate spec files for AWX packages.')
parser.add_argument('build_requires', metavar='build_requires_json', type=str)
parser.add_argument('requires', metavar='requires_json', type=str)
parser.add_argument('pkgs_dir', metavar='packages_directory', type=str)
parser.add_argument('--parse-single', metavar='package_name', type=str)
args = parser.parse_args()

reqs = args.requires
build_reqs = args.build_requires
pkgs_dir = args.pkgs_dir


def generate_spec_for(package_name, reqs, buildreqs, pkgs_dir):
    pkg_dir = glob.glob(f'{pkgs_dir}/{package_name}/{package_name}-*/')[0]
    with open(reqs, 'r') as fp:
        reqs_data = json.load(fp)
        pkg_deps = ' '.join([dep['name']+dep['specifier']+dep['version'] for dep in reqs_data[package_name]['dependencies']])

    with open(buildreqs, 'r') as fp:
        build_reqs_data = json.load(fp)
        pkg_build_deps = ' '.join([dep['name']+dep['specifier']+dep['version'] for dep in build_reqs_data[package_name]['buildrequires']])
    print(pkg_dir)
    command = ["python3", "setup.py", "bdist_rpm", "--spec-only",
               "--build-requires", pkg_build_deps, "--requires",
               pkg_deps, "--packager", PACKAGER, "--dist-dir", "../"]
    print(' '.join(command))
    subprocess.run(command, cwd=pkg_dir)


if args.parse_single:
    generate_spec_for(args.parse_single, reqs, build_reqs, pkgs_dir)
else:
    pass
