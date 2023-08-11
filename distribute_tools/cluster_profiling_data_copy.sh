#!/bin/bash
# Copyright 2023 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SSH="ssh -o StrictHostKeyChecking=no"
SCP="scp -o StrictHostKeyChecking=no"

# Get the node list in the cluster.
get_cluster_list()
{
    local cluster_config=$1
    cat ${cluster_config} | python3 -c 'import sys,json;[print(node) for node in json.load(sys.stdin)["cluster"].keys()]'
}

# Get the account number of node.
get_node_user()
{
    local cluster_config=$1
    local node=$2
    cat ${cluster_config} | python3 -c 'import sys,json;print(json.load(sys.stdin)["cluster"]['\"${node}\"']["user"])'
}

# Get the password of node.
get_node_passwd()
{
    local cluster_config=$1
    local node=$2
    cat ${cluster_config} | python3 -c 'import sys,json;print(json.load(sys.stdin)["cluster"]['\"${node}\"']["passwd"])'
}

# Get the dir of node.
get_node_dir()
{
    local cluster_config=$1
    local node=$2
    cat ${cluster_config} | python3 -c 'import sys,json;print(json.load(sys.stdin)["cluster"]['\"${node}\"']["dir"])'
}

# Copy data from remote node to local node.
rscp_pass()
{
    local node="$1"
    local user="$2"
    local passwd="$3"
    local src="$4"
    local target="$5"
    sshpass -p "${passwd}" ${SCP} -r "${user}"@"${node}":"${src}" "${target}"
}

# 指定拷贝使用的json文件
cluster_account_config_path=$1
# 指定拷贝的路径
target_dir=$2

node_list=$(get_cluster_list ${cluster_account_config_path})
echo "-----begin----"

for node in ${node_list}
do
    user=$(get_node_user ${cluster_account_config_path} ${node})
    passwd=$(get_node_passwd ${cluster_account_config_path} ${node})
    src_dir=$(get_node_dir ${cluster_account_config_path} ${node})
    echo "------------------${user}@${node}---------------------"
    $(rscp_pass ${node} ${user} ${passwd} "${src_dir}" ${target_dir})
done
