#! /bin/sh
#
# getApi.sh
# Copyright (C) 2021 Roman Bulakh <bulah.roman@gmail.com>
#
# Distributed under terms of the MIT license.
#

wget https://raw.githubusercontent.com/osrg/gobgp/master/api/attribute.proto -O api/attribute.proto
wget https://raw.githubusercontent.com/osrg/gobgp/master/api/capability.proto -O api/capability.proto
wget https://raw.githubusercontent.com/osrg/gobgp/master/api/gobgp.proto -O api/gobgp.proto

python -m grpc_tools.protoc -I./api/ --python_out=./api/ --grpc_python_out=./api/ api/*.proto 

ed -i -e 's/import gobgp_pb2/import api.gobgp_pb2/g' api/*py
