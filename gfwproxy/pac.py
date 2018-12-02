import base64
from urllib.request import build_opener

from pyplus.subprocess import shell
from genpac.core import _GFWLIST_URL, parse_rules


def _get_genpac_path(): return shell.run('which genpac', output='str').rstrip('\n')


def gen(pac_file, local_host, local_port, gfwlist_url = _GFWLIST_URL):
    ret = shell.run('{} --proxy="SOCKS5 {}:{}" -o {} --gfwlist-url="{}"'.format(
        _get_genpac_path(), local_host, local_port, pac_file, gfwlist_url))
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))



def fetch_gfwlist(url=_GFWLIST_URL):
    res = build_opener().open(url)
    content = res.read()
    content = base64.b64decode(content).decode('utf-8')
    rules = content.splitlines()[1:]
    rules = parse_rules(rules)
    return rules[0], rules[1]       # direct and proxy




if __name__ == '__main__':
    fetch_gfwlist()