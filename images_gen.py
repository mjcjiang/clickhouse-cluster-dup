import subprocess
import sys
import os
import getopt

ident_map = {
    "shard": 3,
    "replica": 4,
    "host": 5,
    "port": 5,
    "user": 5,
    "password": 5,
    "zoo_node": 2,
    "zoo_host": 3,
    "zoo_port": 3,
}

tab_of_spaces = "    "

zookeeper_temp = """
  zookeeper{index}:
    image: zookeeper:3.5
    container_name: zookeeper{index}
    hostname: zookeeper{index}
    networks:
      clickhouse-network:
        ipv4_address: 172.23.0.{net_index}
"""

multi_zookeeper_temp = """
  zookeeper{index}:
    image: bitnami/zookeeper:latest
    container_name: zookeeper{index}
    environment:
      - ZOO_SERVER_ID={server_id}
      - ALLOW_ANONYMOUS_LOGIN=yes
      - ZOO_SERVERS={zookeeper_servers}
    networks:
      clickhouse-network:
        ipv4_address: 172.23.0.{net_index}
"""

clickhouse_temp = """
  clickhouse{index}:
    image: redmagic039/clickhouse{index}:latest
    container_name: clickhouse{index}
    hostname: clickhouse{index}
    networks:
      clickhouse-network:
        ipv4_address: 172.23.0.{net_index}
    {port_str}
    depends_on:
{zoo_keepers}
"""

port_temp = '''ports:
      - "127.0.0.1:8123:8123"
      - "127.0.0.1:9000:9000"'''

network_temp = """networks:
  clickhouse-network:
    name: clickhouse-network
    ipam:
      config:
        - subnet: 172.23.0.0/24
"""

# gen_multi_zookeepers_str: 
def gen_multi_zookeepers_str(zoo_num):
    res = ""
    for i in range(zoo_num):
        res += "zookeeper" + str(i+1).zfill(2) + ":2888:3888,"
    return res[:-1]

# gen_zookeeper_denpend_list: zookeeper dependent string generate
def gen_zookeeper_denpend_list(zoo_num):
    res = ""
    ident_str = " " * 6
    for i in range(zoo_num):
        res += ident_str + "- " + "zookeeper" + str(i+1).zfill(2) + "\n"
    return res

# gen_composer_yml: generate docker-compose.yml according to node number and zookeeper number
def gen_composer_yml(path, node_num, zoo_num):
    net_index = 10
    res = """version: \"3.8\"
services:"""
    zoo_depends = gen_zookeeper_denpend_list(zoo_num)

    if zoo_num == 1:
        zookeeper_cur = zookeeper_temp.replace("{index}", str(1).zfill(2))
        zookeeper_cur = zookeeper_cur.replace("{net_index}", str(net_index))
        res += zookeeper_cur
        net_index += 1
    else:
        for i in range(zoo_num):
            zookeeper_cur = multi_zookeeper_temp.replace("{index}", str(i+1).zfill(2))
            zookeeper_cur = zookeeper_cur.replace("{server_id}", str(i+1))
            zookeeper_cur = zookeeper_cur.replace("{net_index}", str(net_index))
            zookeeper_cur = zookeeper_cur.replace("{zookeeper_servers}", gen_multi_zookeepers_str(zoo_num))
            res += zookeeper_cur
            net_index += 1
    
    for i in range(node_num):
        clickhouse_cur = clickhouse_temp.replace("{index}", str(i+1).zfill(2))
        clickhouse_cur = clickhouse_cur.replace("{net_index}", str(net_index))
        if i == 0:
            clickhouse_cur = clickhouse_cur.replace("{port_str}", port_temp)
        else:
            clickhouse_cur = clickhouse_cur.replace("{port_str}", "")
            
        clickhouse_cur = clickhouse_cur.replace("{zoo_keepers}", zoo_depends)
        res += clickhouse_cur
        net_index += 1

    res += network_temp
    with open(path, "w") as file:
        file.write(res)

# construct_images: build and push Docker images to repositery for docker swarm use
def construct_images(node_num):
    file_content = ""
    with open("./Dockerfile_temp") as file:
        file_content = file.read()
        
    for i in range(node_num):
        index_str = "0" + str(i+1)
        temp_content = file_content.replace("{num}", index_str)
        with open("./Dockerfile", "w") as file:
            file.write(temp_content)

        #Docker build
        subprocess.run(["docker", "build", "-t", "redmagic039/clickhouse" + index_str, "."])
        #Push to docker hub
        subprocess.run(["docker", "image", "push", "redmagic039/clickhouse" + index_str])
        #Remove Dockerfile
        subprocess.run(["rm", "./Dockerfile"])

# gen_nodes_str: generate cluster node list as a string
def gen_nodes_str(node_num):
    res = ""
    for i in range(node_num):
        res += "clickhouse" + str(i+1).zfill(2) + " "
    return res[0:-1]

# gen_cluster_config_str: generate cluster config string for config.xml
def gen_cluster_config_str(node_num):
    shard_num = node_num // 2
    res = ""
    for i in range(shard_num):
        res += tab_of_spaces * ident_map["shard"] + "<shard>" + "\n"
        for j in range (i * 2, (i + 1) * 2):
            res += tab_of_spaces * ident_map["replica"] + "<replica>" + "\n"
            res += tab_of_spaces * ident_map["host"] + "<host>" + "clickhouse" + str(j+1).zfill(2)  + "</host>" + "\n"
            res += tab_of_spaces * ident_map["port"] + "<port>" + str(9000)  + "</port>" + "\n"
            res += tab_of_spaces * ident_map["user"] + "<user>" + "admin"  + "</user>" + "\n"
            res += tab_of_spaces * ident_map["password"] + "<password>" + "Life123"  + "</password>" + "\n"
            res += tab_of_spaces * ident_map["replica"] + "</replica>" + "\n"
        res += tab_of_spaces * ident_map["shard"] + "</shard>" + "\n"
    return res

# gen_zookeeper_config_str: generate zookeeper config string for config.xml
def gen_zookeeper_config_str(zoo_num):
    res = ""
    for i in range(zoo_num):
        res += tab_of_spaces * ident_map["zoo_node"] + "<node index=\"" + str(i+1) + "\">" + "\n"
        res += tab_of_spaces * ident_map["zoo_host"] + "<host>" + "zookeeper" + str(i+1).zfill(2) + "</host>" + "\n"
        res += tab_of_spaces * ident_map["zoo_port"] + "<port>" + "2181" + "</port>" + "\n"
        res += tab_of_spaces * ident_map["zoo_node"] + "</node>" + "\n"
    return res

# gen_make_file: generate Makefile according to node number
def gen_make_file(node_num):
    with open("Makefile", "w") as file:
        file_content = ".PHONY: config\n"
        file_content += "config:\n"
        file_content += "\trm -rf clickhouse*\n"
        file_content += "\tmkdir -p "
        file_content += nodes_str + "\n"
        for i in range(node_num):
            replica_index = str(i+1).zfill(2)
            shard_index = str(i // 2 + 1).zfill(2)
            file_content += "\tREPLICA=%s SHARD=%s envsubst < config.xml > clickhouse%s/config.xml\n" % (replica_index, shard_index, replica_index)
        for i in range(node_num):
            replica_index = str(i+1).zfill(2)
            file_content += "\tcp users.xml clickhouse%s/users.xml\n" % (replica_index,)
        file.write(file_content)

# regen_temp_config: regenerate config.xml according to node_str
def regen_temp_config(config_path, node_str, zoo_str):
    hole_start = "<clickhouse_cluster>"
    hole_end = "</clickhouse_cluster>"
    new_content = ""
    with open(config_path, "r") as config:
        origin_content = config.read()
        first_start_index = origin_content.index(hole_start) + len(hole_start)
        last_start_index = origin_content.index(hole_end)
        first_half = origin_content[:first_start_index+1]
        second_half = tab_of_spaces * 2 + origin_content[last_start_index:]
        new_content = first_half + node_str + second_half
    with open(config_path, "w") as new_config:
        new_config.write(new_content)

    zoo_start = "<zookeeper>"
    zoo_end = "</zookeeper>"
    new_content = ""
    with open(config_path, "r") as config:
        origin_content = config.read()
        first_start_index = origin_content.index(zoo_start) + len(zoo_start)
        last_start_index = origin_content.index(zoo_end)
        first_half = origin_content[:first_start_index+1]
        second_half = tab_of_spaces * 1 + origin_content[last_start_index:]
        new_content = first_half + zoo_str + second_half
    with open(config_path, "w") as new_config:
        new_config.write(new_content)

if __name__ == "__main__":
    argv = sys.argv[1:]  
    opts, args = getopt.getopt(argv, "s:z:", ["shard_num =", "zookeeper_num ="])

    shard_num = 0
    zoo_num = 0
    for opt, arg in opts:
        if opt in ['-s', '--shard_num']:
            shard_num = int(arg)
        if opt in ['-z', '--zookeeper_num']:
            zoo_num = int(arg)
            
    node_num = 2 * shard_num
    nodes_str = gen_nodes_str(node_num)

    #regen config.xml
    cluster_nodes_str = gen_cluster_config_str(node_num)
    zoo_nodes_str = gen_zookeeper_config_str(zoo_num)
    regen_temp_config("config.xml", cluster_nodes_str, zoo_nodes_str)
    #regen docker-compose.yml
    gen_composer_yml("docker-compose.yml", node_num, zoo_num)
    #generate a Makefile in current dir
    gen_make_file(node_num)
    #do make
    subprocess.run(["make", "config"])
    #construct images and push to docker hub
    construct_images(node_num)
    
