## awx-rpm
Repo for AWX-RPM project


## installed packages
YUM:
python3-requests postgresql-devel

From PIP:
requirements-parser

## Using
In the 'parser' dir:

# Fetch packages and generate dependency list.
python3 ./fetch_packages.py

# Generate spec files
python3 parse.py buildrequires.json out.json packages

