import os
from pyplus.subprocess import shell
from genpac.core import _GFWLIST_URL

_DEFAULT_CONF_DIR = '/etc/privoxy'

_DEFAULT_CONFIG_FILE = os.path.join(_DEFAULT_CONF_DIR, 'config')

_DEFAULT_PAC_ACTION_FILE = os.path.join(_DEFAULT_CONF_DIR, 'gfwlist.action')

def _load_config(config_path):
    with open(config_path, 'r') as f:
        lines = f.readlines()
    return lines

def _save_config(config_path, lines):
    with open(config_path, 'w') as f:
        f.truncate()
        f.writelines(lines)


def _search(lines, *keys):
    for i in range(len(lines)):
        l = lines[i]
        if l.startswith('#'): continue
        splits = l.split()
        if len(splits) < len(keys): continue
        match = True
        for j in range(len(keys)):
            if keys[j] == splits[j]: continue
            match = False
            break
        if match: return i
    return -1



def _pac_on_off(lines, on_off, pac_action_file=_DEFAULT_PAC_ACTION_FILE):
    pac_file = os.path.basename(pac_action_file)
    index = _search(lines, 'actionsfile', pac_file)
    if on_off:
        pac_content = 'actionsfile {}   # User PAC actions [add by gfwproxy]'.format(pac_file)
        if index >= 0: return lines
        if lines[-1].find('\n') < 0: lines[-1] += '\n'
        lines.append(pac_content)
    else:
        if index < 0: return lines
        del lines[index]

    return lines


def _forward_on_off(lines, on_off, ip, port):
    index = _search(lines, 'forward-socks5t', '/')
    if on_off:
        if index >=0: return lines
        lines.append('\n')
        lines.append('forward-socks5t   /               {}:{} .  # Forward to socket5 [add by gfwproxy]'.format(ip, port))
    else:
        if index < 0: return lines
        del lines[index]

    return lines




def set_mode(mode, ip='127.0.0.1', port=1080, config_file=_DEFAULT_CONFIG_FILE, pac_action_file=_DEFAULT_PAC_ACTION_FILE):
    lines = _load_config(config_file)
    if mode == 'pac':
        lines = _forward_on_off(lines, False, ip, port)
        lines = _pac_on_off(lines, True, pac_action_file)

    elif mode == 'global':
        lines = _forward_on_off(lines, True, ip, port)
        lines = _pac_on_off(lines, False, pac_action_file)

    elif mode == 'off':
        lines = _forward_on_off(lines, False, ip, port)
        lines = _pac_on_off(lines, False, pac_action_file)

    else: raise Exception('Invalid mode {}'.format(mode))

    _save_config(config_file, lines)

    # restart privoxy
    ret = shell.run('service privoxy restart')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))


def gen_pac_action(file_path, ip, port, gfwlist_url=_GFWLIST_URL):

    # remove old pac file
    if os.path.isfile(file_path): os.remove(file_path)

    gfwlist2privoxy = os.path.join(os.path.dirname(__file__), 'gfwlist2privoxy')

    ret= shell.run('{} {} {}:{} {}'.format(
        gfwlist2privoxy,
        file_path,
        ip, port,
        gfwlist_url
    ))

    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))



def pid():
    ret = shell.run("ps -ef | grep privoxy | grep -v grep | awk '{print $2}'", output='single')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))

    try:
        return int(ret)
    except:
        return -1