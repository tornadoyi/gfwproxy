import os
import stat
_COMMENT = '#load gfwproxy environments [add by gfwproxy]'



def _search(lines, key):
    for i in range(len(lines)):
        l = lines[i]
        if l.find(key) < 0: continue
        return i
    return -1


def init(user_profile, gfw_profile, local_host='127.0.0.1', http_port=8118, sock_port=1080):

    # load user profile
    with open(user_profile, 'r') as f:
        lines = f.readlines()

    index = _search(lines, _COMMENT)
    if index < 0:
        if lines[-1].find('\n') < 0: lines[-1] += '\n'
        lines.append('source {}    {}\n'.format(gfw_profile, _COMMENT))
    else:
        lines[index] = 'source {}    {}\n'.format(gfw_profile, _COMMENT)

    # save user profile
    with open(user_profile, 'w+') as f:
        f.writelines(lines)


    # save profile of gfwproxy
    lines = [
        'PROXY=0',
        'if [ $PROXY = 1 ]',
        'then',
        '   export http_proxy="{}:{}"'.format(local_host, http_port),
        '   export https_proxy="{}:{}"'.format(local_host, http_port),
        '   export ftp_proxy="{}:{}"'.format(local_host, http_port),
        '   export all_proxy="socks5://{}:{}"'.format(local_host, sock_port),
        'else',
        '   unset http_proxy',
        '   unset https_proxy',
        '   unset ftp_proxy',
        '   unset all_proxy',
        'fi'
    ]

    content = ''
    for l in lines: content += l + '\n'
    with open(gfw_profile, 'w+') as f:
        f.write(content)

    os.chmod(gfw_profile, stat.S_IRWXU)



def proxy_on_off(gfw_profile, on_off):
    # load gfwproxy profile
    with open(gfw_profile, 'r') as f:
        lines = f.readlines()

    index = _search(lines, 'PROXY=')
    lines[index] = 'PROXY={}\n'.format(1 if on_off else 0)

    # save gfwproxy profile
    with open(gfw_profile, 'w+') as f:
        f.writelines(lines)