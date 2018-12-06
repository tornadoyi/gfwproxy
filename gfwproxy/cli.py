import os
import sys
import pwd
import grp
import shutil
import signal
from functools import partial
import argparse

from pyplus.subprocess import shell
from pyplus.collections import qdict
from gfwproxy import pac, privoxy, ss, network, config, profile


_DEFAULT_CONF_DIR = os.path.expanduser('~/.gfwproxy')
_DEFAULT_CONFIG_PATH = os.path.join(_DEFAULT_CONF_DIR, 'gfwproxy.conf')
_DEFAULT_PAC_PATH = os.path.join(_DEFAULT_CONF_DIR, 'gfwproxy.pac')
_DEFAULT_SS_CONFIG_PATH = os.path.join(_DEFAULT_CONF_DIR, 'shadowsocks.conf')
_DEFAULT_GFWPROXY_PROFILE_PATH = os.path.join(_DEFAULT_CONF_DIR, 'gfwproxy.env')


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
    init.add_argument('--profile', type=str, default=None, help='The path of user profile')
    init.add_argument('--user', type=str, default=None, help='Proxy for specific user, default is current user')

    # set mode
    mode = sparser.add_parser('mode', help='Set proxy mode')
    mode.set_defaults(func=partial(_parse_command, 'mode'))
    mode.add_argument('value', type=str, choices=['global', 'pac', 'off'], help='Set specific mode for proxy')
    mode.add_argument('--user', type=str, default=None, help='Proxy for specific user, default is current user')

    # status
    status = sparser.add_parser('status', help='Check proxy status')
    status.set_defaults(func=partial(_parse_command, 'status'))

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

    if args.profile is None:
        print('The path of user profile need to be provided, example ~/.profile')
        args.profile = input('Profile path: ')

    args.profile = os.path.expanduser(args.profile)
    if not os.path.isfile(args.profile): raise Exception('Invalid user profile {}'.format(args.profile))


    # check sslocal
    ret = shell.run('which sslocal')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))

    # check genpac
    ret = shell.run('which genpac')
    if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))

    # create config dir
    if os.path.isdir(_DEFAULT_CONF_DIR): shutil.rmtree(_DEFAULT_CONF_DIR)
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

    # save config
    config.init(_DEFAULT_CONFIG_PATH, profile_path=args.profile)

    # init gfwproxy profile
    profile.init(args.profile, _DEFAULT_GFWPROXY_PROFILE_PATH,
                 local_host=args.local_host, sock_port=args.local_port)


    # set access previlage for current user
    gid = pwd.getpwnam(args.user).pw_gid
    gname = grp.getgrgid(gid).gr_name
    shell.run('chown -R {}:{} {}'.format(args.user, gname, _DEFAULT_CONF_DIR))


def cmd_mode(args):
    mode = args.value

    # load config
    cfg = config.load(_DEFAULT_CONFIG_PATH)
    if mode == cfg['mode']: return

    # load

    ss_cfg = ss.load_config(_DEFAULT_SS_CONFIG_PATH)
    local_host, local_port = ss_cfg['local_address'], ss_cfg['local_port']

    if mode == 'global':
        network.set_mode('manual', args.user, pac_file=_DEFAULT_PAC_PATH, sock_host=local_host, sock_port=local_port)
        privoxy.set_mode('global', local_host, local_port)
        profile.proxy_on_off(_DEFAULT_GFWPROXY_PROFILE_PATH, True)

    elif mode == 'pac':
        network.set_mode('auto', args.user, pac_file=_DEFAULT_PAC_PATH)
        privoxy.set_mode('pac', local_host, local_port)
        profile.proxy_on_off(_DEFAULT_GFWPROXY_PROFILE_PATH, True)

    elif mode == 'off':
        network.set_mode('disabled', args.user)
        privoxy.set_mode('off', local_host, local_port)
        profile.proxy_on_off(_DEFAULT_GFWPROXY_PROFILE_PATH, False)

    else: raise Exception('Invalid mode {}'.format(mode))


    # save mode to config
    cfg['mode'] = mode
    config.save(_DEFAULT_CONFIG_PATH, cfg)



def cmd_status(args):
    cfg = config.load(_DEFAULT_CONFIG_PATH)
    privoxy_id = privoxy.pid()
    privoxy_status = 'stopped' if privoxy_id == -1 else 'start (pid={})'.format(privoxy_id)
    sslocal_id = ss.pid()
    sslocal_status = 'stopped' if sslocal_id == -1 else 'start (pid={})'.format(sslocal_id)


    status = [
        'privoxy: {}'.format(privoxy_status),
        'sslocal: {}'.format(sslocal_status),
        'mode: {}'.format(cfg['mode'])
    ]
    for s in status: print(s)



def _request_sudo(user=None):
    if user is not None: return

    # sudo run command
    sudo_path = shell.run('which sudo', output='single')
    command = '{} {} '.format(sudo_path, sys.executable)
    for arg in sys.argv: command += arg + ' '
    if user is None: command += '--user={} '.format(pwd.getpwuid( os.getuid()).pw_name)
    os.system(command)

    # reload envs
    shell.run('source {}'.format(_DEFAULT_GFWPROXY_PROFILE_PATH))

    # exit
    exit(0)



def main():

    # catch exit signals
    def handle_signals(signum, frame):
        exit(0)
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)


    # parse args
    cmd, args = load_config()
    args = qdict(args)


    # dispatch command
    if cmd == 'init':
        _request_sudo(args.user)
        cmd_init(args)

    elif cmd == 'mode':
        _request_sudo(args.user)
        cmd_mode(args)

    elif cmd == 'status':
        cmd_status(args)

    else: raise Exception('Invalid command {0}'.format(cmd))


if __name__ == '__main__':
    main()




