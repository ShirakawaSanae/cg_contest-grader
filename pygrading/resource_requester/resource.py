import os
import random
import threading
from contextlib import contextmanager
from time import sleep
from typing import Optional

from pygrading import Job
import pygrading
import requests


class Resource:
    def __init__(self, user, ip, port, password):
        self.user = user
        self.ip = ip
        self.port = port
        self.password = password
        self._remote_prefix = f"{self.user}@{self.ip}"
        self._ssh_prefix = f"sshpass -p {self.password} ssh -o StrictHostKeyChecking=no -p {self.port} {self.user}@{self.ip}"
        self._scp_prefix = f"sshpass -p {self.password} scp -o StrictHostKeyChecking=no -P {self.port}"

    def exec(self, command: str):
        return pygrading.exec(f"{self._ssh_prefix} {command}")

    def scp(self, source: str, target: str):
        return pygrading.exec(f"{self._scp_prefix} {source} {target}")

    def upload(self, source: str, target: str):
        return self.scp(source, f"{self._remote_prefix}:{target}")

    def download(self, source: str, target: str):
        return self.scp(f"{self._remote_prefix}:{source}", target)


_manager_server_addr_keys = ["FPGA_SERVER_ADDR", "fpga_server_addr"]
_user_id_keys = ["CGUSER", "CGUSERID", "USER", "USERID", "CGCONTAINER"]


def _get_config(config: dict, keys: list[str], default=None):
    for key in keys:
        if key in config:
            return config[key]
    for key in os.environ:
        if key in os.environ:
            return os.environ[key]
    if default:
        return default
    raise KeyError(keys)


@contextmanager
def resource(job: Job, resource_type: str, timeout: Optional[int]):
    config = job.get_config()
    manager_addr = _get_config(config, _manager_server_addr_keys)
    user_id = _get_config(config, _user_id_keys, "Pygrading" + ''.join(random.sample('abcdefghijklmnopqrstuvwxyz', 10)))
    get_board = requests.get(f'http://{manager_addr}/get-board',
                             params={"userId": user_id, "boardType": resource_type})
    get_board_ans = get_board.json()
    if get_board_ans['result'] != 'OK':
        raise RuntimeError('request to get boards failed')
    if timeout is None:
        timeout = (1 << 32)
    log_id = None
    while timeout > 0:
        get_record = requests.get(f'http://{manager_addr}/my-status',
                                  params={"userId": user_id, "page": 1, "type": "using"})
        get_record_ans = get_record.json()
        if len(get_record_ans['records']) > 0:
            log_id = get_record_ans['records'][0]['id']
            break
        timeout -= 1
        sleep(1)
    if not log_id:
        raise TimeoutError(f"waiting resource {resource_type} timeout.")
    usage = requests.get(f'http://{manager_addr}/get-usage', params={"logId": log_id}).json()
    ssh_usage = [x for x in usage if x['protocol'] == "ssh"]
    if len(ssh_usage) == 0:
        raise RuntimeError(f"No ssh usage of resource:{resource_type} log_id:{log_id}")
    usage = ssh_usage[0]
    if len(ssh_usage) > 1:
        root_usage = [x for x in ssh_usage if x['user' == "root"]]
        usage = root_usage[0] if len(root_usage) > 0 else usage

    try:
        beating = True

        def beat():
            while beating:
                requests.get(f"http://{manager_addr}/beat", params={"userId": user_id})
                sleep(10)

        threading.Thread(target=beat).start()
        yield Resource(usage['user'], usage['ip'], usage['port'], usage['password'])
    finally:
        # 释放资源
        beating = False
        requests.get(f"http://{manager_addr}/release-board", params={"userId": user_id, "boardType": resource_type})
