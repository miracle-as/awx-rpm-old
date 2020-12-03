#!/opt/rh/rh-python36/root/bin/python3
import fileinput
import json
import subprocess

PREFIX = 'awx-python36'
PACKAGER = 'Sinan Sert <sis@miracle.dk>'



def generate_spec_for(package_name, requiresjson):
    pass

with open('out.json') as f:
    data = json.load(f)

with open('buildrequires.json') as f:
    builddata = json.load(f)

arg = 'adal' # sys.argv[1]
pkg_name = data[arg]
bpkg_name = builddata[arg]
deps = (pkg_name['dependencies'])
bdeps = (bpkg_name['buildrequires'])
pkg_dir = f"packages/{pkg_name['name']}/{pkg_name['name']}-{pkg_name['definite_version']}"
spec_file = f"{pkg_name['name']}/{pkg_name['name']}.spec"

requires = ""
for specs in deps:
    requires += str(f"{specs['name']}{specs['specifier']}{specs['version']} ")

buildrequires = ""
for bspecs in bdeps:
    buildrequires += str(f"{bspecs['name']}{bspecs['specifier']}{bspecs['version']} ")


subprocess.run(["python3", "setup.py", "bdist_rpm", "--spec-only",
                "--build-requires", buildrequires, "--requires",
                requires, "--packager", PACKAGER, "--dist-dir", "../"], cwd=pkg_dir)

with fileinput.FileInput(spec_file, inplace=True) as file:
    for line in file:
        print(line.replace("define name "+f"{pkg_name['name']}","define name "+PREFIX+ "-" +f"{pkg_name['name']}"), end='')

file.close()
