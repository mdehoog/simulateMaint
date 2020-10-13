from pprint import pprint
from os import getenv
from atlasapi.atlas import Atlas
from atlasapi.clusters import ClusterConfig, InstanceSizeName, ClusterStates, ShardedClusterConfig, TLSProtocols
from enum import Enum
from typing import List, Optional
from time import sleep
import argparse

ATLAS_USER = getenv("ATLAS_USER", "")
ATLAS_KEY = getenv("ATLAS_KEY", "")
ATLAS_GROUP = getenv("ATLAS_GROUP", "")


class TlsVersions(Enum):
    TLS1_0 = 'TLS1_0'
    TLS1_1 = 'TLS1_1'
    TLS1_2 = 'TLS1_2'
    TLS1_3 = 'TLS1_3'


class Actions(Enum):
    SCALEUP = 'SCALEUP'
    SCALEDOWN = 'SCALEDOWN'
    TLS = 'TLS'

    def __str__(self):
        return self.value


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


class ClusterToScale(object):
    def __init__(self, current_cluster: dict):
        self.cluster_type = current_cluster["clusterType"]
        if self.cluster_type == "SHARDED":
            self.current_config: ClusterConfig = ShardedClusterConfig.fill_from_dict(current_cluster)
        else:
            self.current_config: ClusterConfig = ClusterConfig.fill_from_dict(current_cluster)
        self.current_size = self.current_config.providerSettings.instance_size_name
        try:
            self.size_up: InstanceScale = InstanceScale[
                self.current_config.providerSettings.instance_size_name.name].value
        except ValueError:
            self.size_up = None
            print(f"No upgrade path for {self.current_size.value}")
        try:
            self.size_down = InstanceSizeName[InstanceScale(self.current_size).name]
        except ValueError:
            self.size_down = None
            print(f"No downgrade path for {self.current_size.name}")
        self.name: str = self.current_config.name


class ProjectToScale(object):
    def __init__(self,exclude: Optional[List[str]]):
        self.a = Atlas(ATLAS_USER, ATLAS_KEY, ATLAS_GROUP)
        self.cluster_list = None
        try:
            self.exclude_list = [item.strip() for item in args.exclude[0].split(',')]
        except Exception as e:
            raise e
            self.exclude_list = None

    def get_clusters(self) -> List[ClusterToScale]:
        self.cluster_list = []
        if self.exclude_list is None:
            print("No exclude list")
            for each_cluster in self.a.Clusters.get_all_clusters(iterable=True):
                cluster = ClusterConfig.fill_from_dict(each_cluster)
                if cluster.providerSettings.instance_size_name not in [InstanceSizeName.M0, InstanceSizeName.M2,
                                                                       InstanceSizeName.M5] \
                        and cluster.state_name == ClusterStates.IDLE:
                    scale_cluster = ClusterToScale(each_cluster)
                    self.cluster_list.append(scale_cluster)
        else:
            print(f"Processing exclude list")
            for each_cluster in self.a.Clusters.get_all_clusters(iterable=True):
                cluster = ClusterConfig.fill_from_dict(each_cluster)
                if cluster.providerSettings.instance_size_name not in [InstanceSizeName.M0, InstanceSizeName.M2,
                                                                       InstanceSizeName.M5] \
                        and cluster.state_name == ClusterStates.IDLE:
                    #print(f"Cluster name: {cluster.name}... exclude list: {self.exclude_list}")
                    if cluster.name in self.exclude_list:
                        print(f"Not adding {cluster.name} to the list of clusters to be processed.")
                    else:
                        scale_cluster = ClusterToScale(each_cluster)
                        self.cluster_list.append(scale_cluster)
            print(f"The cluster list now has {len(self.cluster_list)} members")
        return self.cluster_list

    def scale_all_up(self, delay_secs: int = 4):
        if self.cluster_list is None:
            self.get_clusters()
        for each_cluster in self.cluster_list:
            print(
                f"Scaling Up cluster {each_cluster.name} from {each_cluster.current_size.value} to {each_cluster.size_up.value}")
            result = self.a.Clusters.modify_cluster_instance_size(cluster=each_cluster.name,
                                                                  new_cluster_size=each_cluster.size_up)
            if delay_secs > 0:
                print(f"Pausing {delay_secs} seconds")
                sleep(delay_secs)

    def scale_all_down(self, delay_secs: int = 4):
        if self.cluster_list is None:
            self.get_clusters()
        for each_cluster in self.cluster_list:
            print(
                f"Scaling Down cluster {each_cluster.name} from {each_cluster.current_size.value} to {each_cluster.size_down.value}")
            result = self.a.Clusters.modify_cluster_instance_size(cluster=each_cluster.name,
                                                                  new_cluster_size=each_cluster.size_down)
            if delay_secs > 0:
                print(f"Pausing {delay_secs} seconds")
                sleep(delay_secs)

    def change_tls_min(self, tls_version: TLSProtocols = None, delay_secs: int = 4):
        if self.cluster_list is None:
            self.get_clusters()
        if tls_version is None:
            raise (ValueError('You must provide a valid TLSProtocols value.'))

        for each_cluster in self.cluster_list:
            result = self.a.Clusters.modify_cluster_tls(each_cluster.name, TLS_protocol=tls_version)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scale Up or scale down all clusters in an Atlas Project')

    parser.add_argument('Action', type=Actions, choices=list(Actions),
                        help='Scale up or down (UP or DOWN)')
    parser.add_argument('--secs', type=int, help='The number of seconds to delay between clusters', default=1)

    parser.add_argument('--tlsversion', help='The TLS version to set on all clusters.',
                        type=TlsVersions, choices=list(TlsVersions))
    parser.add_argument('--exclude', nargs="+", default=[], help='A comma-separated list of cluster names to exclude')

    args = parser.parse_args()
    if args.exclude is not None:
        print(f'We received an exclude list with {len(args.exclude)} members, they will be excluded from the operation')
        print(args.exclude)
    project_to_scale = ProjectToScale(exclude=args.exclude)
    project_to_scale.get_clusters()
    if args.Action == Actions.SCALEUP:
        print(f'Scaling {len(project_to_scale.cluster_list)} Up, with a {args.secs} second delay!')
        project_to_scale.scale_all_up(delay_secs=args.secs)
    if args.Action == Actions.SCALEDOWN:
        print(f'Scaling {len(project_to_scale.cluster_list)} Down, with a {args.secs} second delay!')
        project_to_scale.scale_all_down(delay_secs=args.secs)

    if args.Action == Actions.TLS:
        pprint(f'Setting {len(project_to_scale.cluster_list)} clusters to TLS : {args.tlsversion}')
        project_to_scale.change_tls_min(args.tlsversion)

