#!/bin/bash

# 汇聚节点的信息 ip地址、用户名、密码、profiling存储路径

get_copy_node()
{
    cat ${config_path} | python3 -c 'import sys,json;[print(node) for node in json.load(sys.stdin)["cluster"].keys()]'
}

get_value_by_key()
{
    local node=$1
    local key=$2
    cat ${config_path} | python3 -c 'import sys,json;print(json.load(sys.stdin)["cluster"]['\"${node}\"']['\"${key}\"'])'
}

config_path=$1
target_dir=$2

node_list=$(get_copy_node ${config_path})
echo "-----begin-copy---"

for node in ${node_list}
do
    user=$(get_value_by_key ${node} "user")
    passwd=$(get_value_by_key ${node} "passwd")
	src_dir=$(get_value_by_key ${node} "dir")
    echo "------------------user:${user}----node:${node}---------------------"
    sshpass -p "${passwd}" scp -o StrictHostKeyChecking=no -r "${user}"@"${node}":"${src_dir}" "${target_dir}"
done
