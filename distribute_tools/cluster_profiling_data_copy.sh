#!/bin/bash

# Copyright (c) 2023, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
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
