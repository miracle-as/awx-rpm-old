
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


def generate_spec_for(package_name, reqs_data, build_reqs_data, pkgs_dir):
    pkg_dir = glob.glob(f'{pkgs_dir}/{package_name}/*/')[0]

    pkg_deps = ' '.join([dep['name']+dep['specifier']+dep['version'] for dep in reqs_data[package_name]['dependencies']])
    pkg_build_deps = ' '.join([dep['name']+dep['specifier']+dep['version'] for dep in build_reqs_data[package_name]['buildrequires']])
    print(pkg_dir)
    command = ["python3", "setup.py", "bdist_rpm", "--spec-only",
               "--build-requires", pkg_build_deps, "--packager", PACKAGER, "--dist-dir", "../"]
    if pkg_deps:
        command += ['--requires', pkg_deps]

    print(' '.join(command))
    subprocess.run(command, cwd=pkg_dir)
    specfile_ = glob.glob(f'{pkgs_dir}/{package_name}/*.spec')[0]
    with open(specfile_, 'r') as specfile:
        temp = specfile.read()
    splitted = temp.split('\n')
    splitted[0] = f'%define name {PREFIX}-{package_name}'
    with open(specfile_, 'w') as specfile:
        specfile.write('\n'.join(splitted))


if __name__ == '__main__':
    with open(reqs, 'r') as fp:
        reqs_data = json.load(fp)
    with open(build_reqs, 'r') as fp:
        build_reqs_data = json.load(fp)

    if args.parse_single:
        generate_spec_for(args.parse_single, reqs_data, build_reqs_data, pkgs_dir)
    else:
        for package in reqs_data:
            generate_spec_for(package, reqs_data, build_reqs_data, pkgs_dir)
