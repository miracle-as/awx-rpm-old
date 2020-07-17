import subprocess
import sys
import os

pkgs_path = '/home/init0/PycharmProjects/pip/packages/' # replace with packages path
mods_path = '/home/init0/PycharmProjects/pip/modules/' # replace with modules path where the custom setuptools is located

pkgs = os.listdir(pkgs_path)

my_env = os.environ.copy()
my_env['PYTHONPATH'] = mods_path

for pkg in pkgs:
    print(f'Parsing {pkg}')
    proc = subprocess.run(['python', 'setup.py'], cwd=pkgs_path+pkg, env=my_env)
