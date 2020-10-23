import glob
import subprocess
import sys
import os

pkgs_path = '/home/init0/PycharmProjects/awx-rpm/setup_requirements_parser/packages/' # replace with packages path
mods_path = '/home/init0/PycharmProjects/awx-rpm/setup_requirements_parser/modules/' # replace with modules path where the custom setuptools is located

pkgs = os.listdir(pkgs_path)

my_env = os.environ.copy()
my_env['PYTHONPATH'] = mods_path

for pkg in pkgs:
    globbed = glob.glob(f"{pkgs_path}{pkg}/**/setup.py")
    if not globbed:
        print(f"{pkg} does not have a glob")
        continue
    pkg_real = globbed[0].rstrip("/setup.py")
    print(f'Parsing {pkg}')
    proc = subprocess.run(['python', 'setup.py'], cwd=f"{pkg_real}", env=my_env)
