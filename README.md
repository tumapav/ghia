# GHIA III.
A tool for automatic issue assigning of GitHub issues

## Installation
Install package `ghia-tumapav3` using pip (test PyPi).
```
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple ghia-tumapav3
```

## Usage - CLI
Use `ghia` command to run the cli script. To view help, use `ghia --help`.

**More information at:**
https://github.com/cvut/ghia/tree/basic


## Usage - WEB
Export these environment variables and run the Flask web server:
```
export FLASK_APP=ghia
export GHIA_CONFIG=config.cfg
flask run
```

Where `config.cfg` is a GHIA configuration file. Example is bellow or visit link at the bottom for the full specs.
```
[github]
token=###
secret=###

[patterns]
tester=
    title:network
    text:network
    text:protocol
    text:http[s]{0,1}://localhost:[0-9]{2,5}
    label:^(network|networking)$

[fallback]
label=X-Need assignment
```

**More information at:**
https://github.com/cvut/ghia/tree/web

