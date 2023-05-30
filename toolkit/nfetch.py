#!/usr/bin/env python
# coding: utf-8

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
import yaml

WEB_POOLS = [
    "https://github.com/mianfeifq/share",
    "https://github.com/aiboboxx/v2rayfree",
    "https://github.com/freefq/free",
    "https://github.com/abshare/abshare.github.io",
    "https://github.com/githubvpn007/v2rayNvpn",
    "https://github.com/VpnNetwork01/vpn-net",
    "https://github.com/Pawdroid/Free-servers",
    "https://github.com/tolinkshare/freenode",
    "https://github.com/mksshare/mksshare.github.io",
]


# get working directory
WORK_DIR = Path(__file__).resolve().parent
CONFS_DIR = WORK_DIR / "confs"
CACHE_DIR = WORK_DIR / "cache"

# make dir if not exists
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CONFS_DIR.mkdir(parents=True, exist_ok=True)

# recording files
OK_JSON_FILE = WORK_DIR / "ok.json"
TEST_OK_FILE = WORK_DIR / "test.ok"
TTOK_FILE = WORK_DIR / ".ttok"
OUTBOUND_FILE = CONFS_DIR / "outbound.json"

DATA_DIR = Path("/home/azer/source/free.proxy.2023/")


def load_outbound(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data["outbounds"]


def merge_gen_ok_all():
    outbounds = []
    with open(TEST_OK_FILE, mode="r", encoding="utf-8") as file:
        for line in file:
            server = line.strip()
            if not server or server.startswith("/*"):
                continue

            server_file = CACHE_DIR / f"outbound.{server}.json"
            for outbound in load_outbound(server_file):
                outbounds.append(outbound)

    with open(OK_JSON_FILE, mode="w", encoding="utf-8") as out:
        print(json.dumps({"outbounds": outbounds}), file=out)


# generate ok.json from test.ok
def merge_gen_ok(okfiles=None):
    if not okfiles:
        okfiles = [TEST_OK_FILE]
    outbound = Outbound("vmess")
    ok_obfiles = []
    for okfile in okfiles:
        with open(okfile, mode="r", encoding="utf-8") as file:
            for line in file:
                server = line.strip()
                if not server or server.startswith("/*"):
                    continue

                server_file = CACHE_DIR / f"outbound.{server}.json"
                ok_obfiles.append(server_file)
                for rec in load_outbound(server_file):
                    for node in rec["settings"]["vnext"]:
                        outbound.add(node)

    with open(OK_JSON_FILE, "w", encoding="utf-8") as out:
        print(json.dumps({"outbounds": [outbound.data]}), file=out)

    print("|".join(ofile.as_posix() for ofile in ok_obfiles))


def get_yaml_file():
    for filename in os.listdir(DATA_DIR):
        if filename.endswith((".yml", ".yaml")):
            yield DATA_DIR / filename


def get_recent_file():
    name = ""
    num = 0
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith((".yml", ".yaml")):
            continue
        count = int(filename[:4])
        if num < count:
            name = filename
            num = count
    if name:
        yield DATA_DIR / name


class Vnext:
    def __init__(self, server, port, uuid, aid, protocol="vmess"):
        self.address = server
        self.port = port
        self.uuid = uuid
        self.aid = aid
        self.protocol = protocol

    @property
    def data(self):
        return {
            "address": self.address,
            "port": int(self.port),
            "users": [
                {
                    "id": self.uuid,
                    "alterId": int(self.aid),
                }
            ],
        }

    @property
    def outbound(self):
        return {
            "protocol": self.protocol,
            "settings": {
                "vnext": [
                    self.data,
                ]
            },
        }


class Outbound:
    def __init__(self, protocol="vmess"):
        self.protocal = protocol
        self.vnexts = []

    def add(self, vnext):
        self.vnexts.append(vnext)

    def add_node(self, node):
        self.vnexts.append(node.data)

    @property
    def data(self):
        return {
            "protocol": self.protocal,
            "settings": {
                "vnext": self.vnexts,
            },
        }


def get_node(data):
    addr = data["add"]
    port = data["port"]
    uuid = data["id"]
    altid = data["aid"]
    return Vnext(addr, port, uuid, altid)


def str_constructor(loader, node):
    """Construct a greeting."""
    return f"{loader.construct_scalar(node)}"


# Register the constructor for the !<str> tag
yaml.add_constructor("str", str_constructor)


def get_node_from_yaml(filename):
    with open(filename, encoding="utf-8") as file:
        try:
            data = yaml.full_load(file)
        except yaml.constructor.ConstructorError as e:
            print("Error File:", filename, e, file=sys.stderr)
            raise

        proxys = data["proxies"]
        for proxy in proxys:
            try:
                protocol = proxy["type"]
                if protocol != "vmess":
                    continue
                server = proxy["server"]
                if not is_digit(server):
                    continue
                uuid = proxy["uuid"]
                port = proxy["port"]
                aid = proxy["alterId"]
            except KeyError as e:
                print("KeyError:", proxy, e, file=sys.stderr)
                continue

            yield Vnext(protocol=protocol, server=server, port=port, uuid=uuid, aid=aid)


def get_outbound_one(filename):
    for node in get_node_from_yaml(filename):
        if node.protocol != "vmess":
            continue
        yield node.outbound


def get_outbound_all(filename):
    outbound = None
    for node in get_node_from_yaml(filename):
        if node.protocol != "vmess":
            continue
        if outbound is None:
            outbound = Outbound(protocol=node.protocol)

        outbound.add(node.data)

    return outbound


def check_filenames(filenames):
    match filenames:
        case []:
            return get_recent_file()
        case filenames if isinstance(filenames, str):
            return [filenames]
        case None | ["all"]:
            return get_yaml_file()
        case _:
            return filenames


# generate node from yaml file
def gen_outbound(filenames=None):
    nodes = {}
    filenames = check_filenames(filenames)

    for filename in filenames:
        for node in get_node_from_yaml(filename):
            if node.address not in nodes:
                nodes[node.address] = {"count": 0, "ports": {}}

            if node.port not in nodes[node.address]["ports"]:
                nodes[node.address]["ports"] = {
                    "count": 0,
                }
            nodes[node.address]["count"] += 1
            nodes[node.address]["ports"]["count"] += 1
            nodes[node.address]["ports"][node.port] = node

    outfiles = []
    for address, node in nodes.items():  # 按照server address 进行归类
        outbound = Outbound(protocol="vmess")
        port = ""
        for port in node["ports"]:
            if port == "count":
                continue
            outbound.add(node["ports"][port].data)

        outfile = CACHE_DIR / f"outbound.{address}:{port}.json"
        if outfile.exists():
            continue

        outfiles.append(outfile)
        with open(outfile, mode="w", encoding="utf-8") as out:
            print(json.dumps({"outbounds": [outbound.data]}), file=out)

        valid_vmess(outfile)

    print("|".join(ofile.as_posix() for ofile in outfiles))


def find_content(cont):
    mark = b"ata-snippet-clipboard-copy-content="
    start = 0
    while True:
        start = cont.find(mark, start)
        if start == -1:
            break
        end = cont.find(b">", start)

        bnodes = cont[start + len(mark) : end]
        bnodes = bnodes.strip(b'"')
        yield bnodes
        start = end + 1


def get_vmess(web):
    if not web.startswith("https://"):
        web = f"https://www.github.com/{web}"
    cont = requests.get(web).content

    vmark = b"vmess://"
    for bnodes in find_content(cont):
        for bnode in bnodes.split(b"\n"):
            if not bnode.startswith(vmark):
                continue
            data = base64.urlsafe_b64decode(bnode[len(vmark) :])

            res = data.decode("utf-8", errors="ignore")
            try:
                yield json.loads(res)
            except json.decoder.JSONDecodeError:
                continue


def is_digit(server: str):
    return server.replace(".", "").isdigit()


def process_pools():
    for web in WEB_POOLS:
        yield from get_vmess(web)


# fetch node from github
def fetch():
    outfiles = []
    for web in WEB_POOLS:
        for vmess in get_vmess(web):
            node = get_node(vmess)
            address = node.address
            if not is_digit(address):
                continue
            outfile = CACHE_DIR / f"outbound.{address}:{node.port}.json"
            if outfile.exists():
                continue

            outfiles.append(outfile)
            outbound = Outbound()
            outbound.add_node(node)
            with open(outfile, mode="w", encoding="utf-8") as out:
                print(json.dumps({"outbounds": [outbound.data]}), file=out)

            valid_vmess(outfile)

    if outfiles:
        print("|".join(ofile.as_posix() for ofile in outfiles))


def process_line(line: str):
    start = 0
    while True:
        pos = line.find(": ", start)
        if pos == -1:
            break
        end = line.find(" ", pos + 3)
        if end == -1:  # end of line
            yield line[start:].split(": ")
            break
        yield line[start:end].split(": ")
        start = end + 1


def process_output(output: str):
    for line in output.split("\n"):
        if line.startswith("Current Server"):
            line = line[len("Current Server") + 1 :]
        elif line.startswith("Result:"):
            line = line[len("Result:") + 1 :]
        else:
            continue
        yield dict(process_line(line))


# check node is available
def valid_vmess(filenames: str | Path, okfile: str | Path = TEST_OK_FILE):
    VALID_CMD = WORK_DIR / "../stairspeedtest/stairspeedtest"
    if isinstance(filenames, Path):
        filenames = filenames.as_posix()
    for vms in bytes(filenames, "utf-8").split(b"|"):
        res = subprocess.run(VALID_CMD, input=vms + b"\naa\n", capture_output=True)
        server = ""
        for kws in process_output(res.stdout.decode("utf-8")):
            if "Remarks" in kws:
                server = kws["Remarks"]
                continue
            if "Blocked" == kws.get("NAT Type"):
                print(f"Sever: {server} Blocked")
                continue
            print(f"Sever: {server}", kws)

            # add server ip to TEST_OK_FILE
            os.system(f"echo {server} >> {okfile}")


def clear_TTOK_FILE():
    if TTOK_FILE.exists():
        os.system(f"rm {TTOK_FILE}")


def test_ok(okfiles=None):
    if not okfiles:
        okfiles = [TEST_OK_FILE]
    clear_TTOK_FILE()
    for okfile in okfiles:
        if isinstance(okfile, str):
            okfile = Path(okfile)
        for server in reversed(list(get_servers_from_pfile(okfile))):
            if not server or server.startswith("/*"):
                continue

            server_file = CACHE_DIR / f"outbound.{server}.json"
            if not server_file.exists():
                continue
            valid_vmess(server_file, TTOK_FILE)


def get_servers_from_pfile(pfile: Path):
    if pfile.exists():
        with open(pfile, mode="r", encoding="utf-8") as f:
            for line in f:
                yield line.strip()


def get_servers():
    yield from get_servers_from_pfile(TTOK_FILE)
    yield from reversed(list(get_servers_from_pfile(TEST_OK_FILE)))


def do_enable(servers=None):
    if not servers:
        servers = get_servers()

    for server in servers:
        server_file = CACHE_DIR / f"outbound.{server}.json"
        if not server_file.exists():
            print(f"Server: {server} can not find file: {server_file}", file=sys.stderr)
            continue
        os.system(f"cp {server_file} {OUTBOUND_FILE}")
        print(f"setting done: {server_file}", file=sys.stderr)
        break


def show_usage():
    print(f"Usage: {__file__} subcommand [opts]")
    print("      available command: yaml, genok, fetch, testok, enable")


def app():
    subcmd = sys.argv[1:2]
    match subcmd:
        case ["yaml"] | ["y"]:
            gen_outbound(filenames=sys.argv[2:])

        case ["genok"] | ["ok"]:  # generate outbound file from test.ok file
            merge_gen_ok(okfiles=sys.argv[2:])

        case ["fetch"] | ["f"]:  # fetch new available free server address
            fetch()

        case ["testok"] | ["t"]:
            test_ok(okfiles=sys.argv[2:])

        case ["enable"] | ["e"]:
            do_enable(sys.argv[2:])

        case _:  # show help info
            show_usage()


if __name__ == "__main__":
    app()
