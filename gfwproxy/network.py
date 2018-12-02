from pyplus.subprocess import shell


def set_mode(mode,
             pac_file=None,
             sock_host=None, sock_port=None):
    cmds = []
    if mode == 'auto':
        if pac_file is None: raise Exception('Invalid PAC file path')
        cmds.append('gsetting set org.gnome.system.proxy mode auto')
        cmds.append('gsetting set org.gnome.system.proxy autoconfig-url "file://{}"'.format(pac_file))

    elif mode == 'disabled':
        cmds.append('gsetting set org.gnome.system.proxy mode none')

    elif mode == 'manual':
        if sock_host is None or sock_port is None: raise Exception('Invalid host and port of socks')
        cmds.append('gsetting set org.gnome.system.proxy mode manual')
        cmds.append('gsetting set org.gnome.system.proxy.socks host {}'.format(sock_host, sock_port))

    else: raise Exception('Invalid mode {}'.format(mode))

    for cmd in cmds:
        ret = shell.run(cmd)
        if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))