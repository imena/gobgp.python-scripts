#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 Roman Bulakh <bulah.roman@gmail.com>

"""
connect to GoBGP api and get subnet -> asn data
"""

import os
import argparse
import grpc

import api.gobgp_pb2 as gobgp_pb2
import api.attribute_pb2 as attribute_pb2
import api.gobgp_pb2_grpc as gobgp_pb2_grpc

_TIMEOUT_SECONDS = 1000

def getAnnounces(family: str, goBgpApiUrl: str):
    """
    get request to GoBGP and get list of prefixes
    """
    if family not in ["inet", "inet6"]:
        print(f"ERROR: wrong family: {family}.\nAvailable: inet, inet6")
        return ""

    channel = grpc.insecure_channel(goBgpApiUrl)
    stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    if family == "inet":
        request = stub.ListPath(
            gobgp_pb2.ListPathRequest(
                family=gobgp_pb2.Family(
                    afi=gobgp_pb2.Family.AFI_IP,
                    safi=gobgp_pb2.Family.SAFI_UNICAST
                )
            )
        )
    if family == "inet6":
        request = stub.ListPath(
            gobgp_pb2.ListPathRequest(
                family=gobgp_pb2.Family(
                    afi=gobgp_pb2.Family.AFI_IP6,
                    safi=gobgp_pb2.Family.SAFI_UNICAST
                )
            )
        )

    paths = list(request)

    return paths


def unmarshalAsPath(msg):
    """
    unmarshal as-path attribute from protobuf
    """
    if msg is None:
        return None

    result = attribute_pb2.AsPathAttribute()
    msg.Unpack(result)
    return result

def getSubnetAsn(paths: list):
    """
    create tuple ip_subnet -> ASN
    """
    result = {}
    for path in paths:
        prefix = path.destination.prefix
        destination = path.destination

        if destination.paths[0].pattrs[1].type_url.split('.')[-1] == "AsPathAttribute":
            asPath = unmarshalAsPath(destination.paths[0].pattrs[1])
        else:
            print("ERROR \n", destination.paths[0].pattrs[1])

        if len(asPath.segments) < 1:
            print(prefix)
            print(destination)
            print("ERROR, preffix not have as-path", asPath.segments)
        else:
            segment = asPath.segments[0].numbers
            if len(segment) > 1:
                asn = segment[-1]
            else:
                asn = segment[0]
            # print('Prefix: {}, Source ASN: {}'.format(prefix, asn))
            result[prefix] = asn

    return result

def createIpAsnCsv(filePath: str, data: tuple):
    """
    create CSV file with ipSubnet,asn
    """
    if not os.path.exists(filePath):
        try:
            with open(filePath, "w+") as f:
                f.write("")
                f.close()
        except IOError as E:
            print(f"[ERROR] unable create file {filePath}: {E}")
            return
    if not os.access(filePath, os.W_OK):
        print(f"[ERROR] file {filePath} not writable")
        return

    with open(filePath, "w+") as csv:
        csv.write("network,asn\n")
        for item in data:
            csv.write(f"{item},{data[item]}\n")

    csv.close()

def parseArgs():
    """
    parse arguments and generate files
    """
    parser = argparse.ArgumentParser(prog="getSubnetToAsn",description="Generate IPv4 or IPv6 subnet ratio to ASN")
    parser.add_argument("--gobgp-api", type=str, required=True, help="GoBGP ip:port string. Example: 127.0.0.1:51001")
    parser.add_argument("--family", type=str, required=True, help="Address family: inet, inet6")
    parser.add_argument("--csv-file", type=str, required=True, help="CSV file destination")
    args = parser.parse_args()

    if args.family not in ["inet", "inet6"]:
        print("[ERROR] use family inet or inet6")
        return

    routes = getAnnounces(args.family, args.gobgp_api)
    prefixes = getSubnetAsn(routes)
    createIpAsnCsv(args.csv_file, prefixes)


if __name__ == "__main__":
    # createIpAsnCsv("inet6", "")
    parseArgs()
