import os
import json
from pyplus.subprocess import shell

_SSLOCAL_SERVICE = 'sslocal.service'


def _get_sslocal_path(): return shell.run('which sslocal', output='single')


def stop():
    ret = shell.run('systemctl stop {}'.format(_SSLOCAL_SERVICE))
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))


def start():
    # start sslocal
    ret = shell.run('systemctl start {}'.format(_SSLOCAL_SERVICE))
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))


def pid():
    ret = shell.run("ps -ef | grep sslocal | grep -v grep | awk '{print $2}'", output='single')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))

    try:
        return int(ret)
    except:
        return -1



def load_config(path):
    with open(path, 'r') as f:
        config = json.load(f)
    return config


def gen_config(config_path,
                    server, server_port, password,
                    local_address="127.0.0.1", local_port=1080,
                    timeout=300, method="AES-256-CFB"):
    cfg = {
        "server": server,
        "server_port": server_port,
        "local_address": local_address,
        "local_port": local_port,
        "password": password,
        "timeout": timeout,
        "method": method
    }

    # create path
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # delete old file
    if os.path.isfile(config_path): os.remove(config_path)

    # create new file
    with open(config_path, 'w+') as f:
        json.dump(cfg, f, indent=4)

    return cfg



def enable_autostart():
    ret = shell.run('systemctl enable {}'.format(_SSLOCAL_SERVICE))
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))


def disable_autostart():
    ret = shell.run('systemctl disable {}'.format(_SSLOCAL_SERVICE))
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))


def add_autostart(ss_config_path):

    service_content = '[Unit] \n' + \
                      'Description=sslocal \n' +\
                      'After=network.target \n' + \
                      '\n' + \
                      '[Service] \n' + \
                      'Type=forking \n' + \
                      'ExecStart={} -c {} -d start \n'.format(_get_sslocal_path(), ss_config_path) + \
                      'ExecStop={} -c {} -d stop \n'.format(_get_sslocal_path(), ss_config_path) + \
                      '\n' + \
                      '[Install] \n' + \
                      'WantedBy=multi-user.target  \n'



    service_path = os.path.join('/etc/systemd/system', _SSLOCAL_SERVICE)
    with open(service_path, 'w') as f:
        f.write(service_content)

    # reload
    ret = shell.run('systemctl daemon-reload')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))

    # set autostart
    enable_autostart()

    # restart
    stop()
    start()



def bug_fix():
    import shadowsocks
    ss_path = os.path.dirname(shadowsocks.__file__)
    openssl_file = os.path.join(ss_path, 'crypto', 'openssl.py')

    with open(openssl_file, 'r') as f:
        content = f.read()

    with open(openssl_file, 'w+') as f:
        content = content.replace('cleanup', 'reset')
        f.write(content)
