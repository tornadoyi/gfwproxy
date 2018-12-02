import os
import sys
import signal
from functools import partial
import argparse

from pyplus.subprocess import shell
from pyplus.collections import qdict
from gfwproxy import pac, privoxy, ss, network


_DEFAULT_CONF_DIR = '/etc/gfwproxy'
_DEFAULT_CONFIG_PATH = os.path.join(_DEFAULT_CONF_DIR, 'gfwproxy.conf')
_DEFAULT_PAC_PATH = os.path.join(_DEFAULT_CONF_DIR, 'gfwproxy.pac')
_DEFAULT_SS_CONFIG_PATH = os.path.join(_DEFAULT_CONF_DIR, 'shadowsocks.conf')



def load_config():

    def _parse_command(cmd, args): return (cmd, args)

    # main parser
    parser = argparse.ArgumentParser(prog='gfwproxy', description="A tool dedicated for pass through chinese Great Fire Wall")
    sparser = parser.add_subparsers()

    # config
    init = sparser.add_parser('init', help='Initialize gfwproxy')
    init.set_defaults(func=partial(_parse_command, 'init'))
    init.add_argument('--proxy-host', type=str, help='Shadowsocks proxy server host')
    init.add_argument('--proxy-port', type=int, help='Shadowsocks proxy server port')
    init.add_argument('--local-host', type=str, default='127.0.0.1', help='Local host')
    init.add_argument('--local-port', type=int, default=1080, help='Local port')
    init.add_argument('--proxy-timeout', type=int, default=300, help='Shadowsocks timeout')
    init.add_argument('--proxy-password', type=str, help='Shadowsocks proxy password')
    init.add_argument('--proxy-method', type=str, default='AES-256-CFB', help='Shadowsocks proxy encrypt method')

    # start
    mode = sparser.add_parser('mode', help='Set proxy mode')
    mode.set_defaults(func=partial(_parse_command, 'mode'))
    mode.add_argument('value', type=str, choices=['global', 'pac', 'direct'], help='Set specific mode for proxy')

    args = parser.parse_args()
    if getattr(args, 'func', None) is None:
        parser.print_help()
        sys.exit(0)

    return args.func(args)



def cmd_init(args):
    if args.proxy_host is None:
        print('Proxy server host of shadowsocks need to be provided')
        args.proxy_host = input('Proxy host: ')

    if args.proxy_port is None:
        print('Proxy server port of shadowsocks need to be provided')
        args.proxy_port = int(input('Proxy port: '))

    if args.proxy_password is None:
        print('proxy password of shadowsocks need to be provided')
        args.proxy_password = input('Proxy password: ')


    # check sslocal
    ret = shell.run('which sslocal')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))

    # check genpac
    ret = shell.run('which genpac')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))

    # create config dir
    os.makedirs(_DEFAULT_CONF_DIR, exist_ok=True)

    # bug fix for shadowsocks
    ss.bug_fix()

    # gen pac
    pac.gen(_DEFAULT_PAC_PATH, args.local_host, args.local_port)

    # get gfwlist
    direct_list, proxy_list = pac.fetch_gfwlist()

    # gen shadowsocks config
    ss.gen_config(_DEFAULT_SS_CONFIG_PATH,
                  server=args.proxy_host,
                  server_port=args.proxy_port,
                  password=args.proxy_password,
                  local_address=args.local_host,
                  local_port=args.local_port,
                  timeout=args.proxy_timeout,
                  method=args.proxy_method)

    # gen pac action
    privoxy.gen_pac_action(privoxy._DEFAULT_PAC_ACTION_FILE,
                           args.local_host, args.local_port, proxy_list)

    # add sslocal to autostart
    ss.add_autostart(_DEFAULT_SS_CONFIG_PATH)


def cmd_mode(args):
    mode = args.value

    ss_cfg = ss.load_config(_DEFAULT_SS_CONFIG_PATH)
    local_host, local_port = ss_cfg['local_address'], ss_cfg['local_port']

    if mode == 'global':
        network.set_mode('manual', pac_file=_DEFAULT_PAC_PATH, sock_host=local_host, sock_port=local_port)
        privoxy.set_mode('global', local_host, local_port)

    elif mode == 'pac':
        network.set_mode('auto', pac_file=_DEFAULT_PAC_PATH)
        privoxy.set_mode('pac', local_host, local_port)

    elif mode == 'direct':
        network.set_mode('disabled')
        privoxy.set_mode('direct', local_host, local_port)

    else: raise Exception('Invalid mode {}'.format(mode))




def main():

    # catch exit signals
    def handle_signals(signum, frame):
        exit(0)
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)


    # check sudo
    uname = shell.run("whoami", output='str').rstrip('\n')
    if uname != 'root':
        print('Need sudo privileges')
        return

    cmd, args = load_config()
    args = qdict(args)

    if cmd == 'init':
        cmd_init(args)

    elif cmd == 'mode':
        cmd_mode(args)

    else: raise Exception('Invalid command {0}'.format(cmd))


if __name__ == '__main__':
    main()




