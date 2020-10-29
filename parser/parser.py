#!/opt/rh/rh-python36/root/bin/python3
import json
import sys
import subprocess
import fileinput

with open('out.json') as f:
    data = json.load(f)

with open('parser.json') as f:
    config = json.load(f)

prefix = (config['prefix'])
packager = (config['packager'])
arg = sys.argv[1]
pkg_name = data[arg]
deps = (pkg_name['dependencies'])
pkg_dir = (f"{pkg_name['name']}/{pkg_name['name']}-{pkg_name['definite_version']}")
spec_file = (f"{pkg_name['name']}/{pkg_name['name']}.spec")

requires = ""
for specs in deps:
    requires += str(f"{specs['name']}{specs['specifier']}{specs['version']} ")

subprocess.run(["python3", "setup.py", "bdist_rpm", "--spec-only","--requires",
                requires, "--packager", packager, "--dist-dir", "../"], cwd=pkg_dir)

with fileinput.FileInput(spec_file, inplace=True) as file:
    for line in file:
        print(line.replace("define name "+f"{pkg_name['name']}","define name "+prefix+ "-" +f"{pkg_name['name']}"), end='')

file.close ()
