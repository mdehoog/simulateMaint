## Simple Atlas Maintenance Simulation script

Uses the Atlas API to simulate two types of common maintenance for an entire project.

1. Using the "SCALEUP" or "SCALEDOWN" actions, simulates a virtual host replacement (stop/start).

2. Using the `TLS` and `--tlsversion` option simulates a mongod/mongos process restart, such as those done during
patch version upgrade (4.4.0 to 4.4.1 for example.)


You can use the `--exclude` option to exclude clusters from the operation. Use a comma separated list of cluster names.
For exmple:
```shell
main.py TLS --tlsversion=TLS1_1 --exclude=Cluster0,Cluster1
```




## Atlas Configuraation 
```python
from os import getenv

ATLAS_USER = getenv("ATLAS_USER", "")
ATLAS_KEY = getenv("ATLAS_KEY", "")
ATLAS_GROUP = getenv("ATLAS_GROUP", "")
```
Takes Atlas API values from the os environment, or can be specified in the file itself.


## Scale Steps
```python
class InstanceScale(Enum):
    M10 = InstanceSizeName.M20
    M20 = InstanceSizeName.M30
    M30 = InstanceSizeName.R40
    M40 = InstanceSizeName.M50
    R40 = InstanceSizeName.R50
    R50 = InstanceSizeName.R60
    M60 = InstanceSizeName.M80
    R60 = InstanceSizeName.R80
    R80 = InstanceSizeName.M140
    M100 = InstanceSizeName.M140
    M140 = InstanceSizeName.M200
    M200 = InstanceSizeName.M300
    M300 = InstanceSizeName.R400
    R400 = InstanceSizeName.R700
```
This Enum maps steps, both up and down. To change the steps, modify this enum accordingly. The defaults 
do not coverall sizes.


```shell script
usage: main.py [-h] [--secs SECS] [--tlsversion {TlsVersions.TLS1_0,TlsVersions.TLS1_1,TlsVersions.TLS1_2,TlsVersions.TLS1_3}] [--exclude EXCLUDE [EXCLUDE ...]] {SCALEUP,SCALEDOWN,TLS}

Perform actions on all clusters in an Atlas Project which simulate maintenance

positional arguments:
  {SCALEUP,SCALEDOWN,TLS}
                        The action to take, either scale up one step, scale down one step, or set TLS min. version.

optional arguments:
  -h, --help            show this help message and exit
  --secs SECS           The number of seconds to delay between clusters
  --tlsversion {TlsVersions.TLS1_0,TlsVersions.TLS1_1,TlsVersions.TLS1_2,TlsVersions.TLS1_3}
                        The TLS version to set on all clusters.
  --exclude EXCLUDE [EXCLUDE ...]
                        A comma-separated list of cluster names to exclude


```