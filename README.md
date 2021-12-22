# AlienSwarm(异星蜂群)
AlienSwarm is a toolset to build *clickhouse* data cluster. You can freely choose your shard number 
and zookeeper number, the toolset will generate all the infrastructures for you.

## 1.requirments:
* python > 3.8
* docker desktop(Windows, Macos, Linux) and docker runtime
* docker hub account (if you do not have, quick register one!)
* three node(bare metal or virtual) which each member can ping with each other

## 2.cluster topology:
In this article, we will build a three node clickhouse cluster(1 manager, 2 worker). The manager node will distribute
4 clickhouse containers(2 shards, 2 replicas each shard) to worker nodes. Also, the manager will distribute 2 zookeeper
containers to work nodes. The structure of the cluster is:

![cluster_structure](./pics/cluster_structure.png)

Wow! The privious picture just captures a state of the cluster, the real cluster may present some different topological structure.

## 3.infra construct:
The *infra_construct.py* script do the following tasks:
* build out clickhouse images and push to docker hub;
* gen *docker-compose.yml* for docker swarm;

run the following command:
```bash
python infra_construct.py -s 2 -z 2
```
1. -s: shard number
2. -z: zookeeper number

![infra_run](./pics/infra_run.png)
