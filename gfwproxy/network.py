from pyplus.subprocess import shell



def set_mode(mode, user,
             pac_file=None,
             sock_host=None, sock_port=None):

    # env commands
    export_proxy_cmds = [
        'export http_proxy="{}:{}"'.format(sock_host, 8118),
        'export https_proxy="{}:{}"'.format(sock_host, 8118),
        'export ftp_proxy="{}:{}"'.format(sock_host, 8118),
        'export all_proxy="socks5://{}:{}"'.format(sock_host, sock_port)
    ]
    unset_proxy_cmds = [
        'unset http_proxy',
        'unset https_proxy',
        'unset ftp_proxy',
        'unset all_proxy',
    ]


    cmds = []
    if mode == 'auto':
        if pac_file is None: raise Exception('Invalid PAC file path')
        cmds.append('gsettings set org.gnome.system.proxy mode auto')
        cmds.append('gsettings set org.gnome.system.proxy autoconfig-url "file://{}"'.format(pac_file))
        cmds += export_proxy_cmds

    elif mode == 'disabled':
        cmds.append('gsettings set org.gnome.system.proxy mode none')
        cmds += unset_proxy_cmds

    elif mode == 'manual':
        if sock_host is None or sock_port is None: raise Exception('Invalid host and port of socks')
        cmds.append('gsettings set org.gnome.system.proxy mode manual')
        cmds.append('gsettings set org.gnome.system.proxy.socks host {}'.format(sock_host, sock_port))
        cmds += export_proxy_cmds

    else: raise Exception('Invalid mode {}'.format(mode))

    # run with user
    with_user_cmd = 'su - {}'.format(user) + ' -c "{}"'

    for cmd in cmds:
        ret = shell.run(with_user_cmd.format(cmd))
        if isinstance(ret, shell.CmdRunError): raise Exception(str(ret))