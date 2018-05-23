import subprocess
import json


def get_keys(uuid):
    data = subprocess.check_output(['openstack', 'console', 'log', 'show', uuid]).decode('utf8')
    lines = data.split('\n')
    cut_a = lines.index('-----BEGIN SSH HOST KEY KEYS-----')
    cut_b = lines.index('-----END SSH HOST KEY KEYS-----')
    return lines[cut_a + 1:cut_b]


hosts = json.loads(subprocess.check_output(['openstack', 'server', 'list', '--name', 'vgcn.*', '-f', 'json']).decode('utf8'))
for host in hosts:
    ip_address = [x.split('=')[1] for x in host['Networks'].split(',')]
    name = host['Name']
    keys = get_keys(host['ID'])

    for key in keys:
        print('%s %s' % (name, key))

    for ip in ip_address:
        for key in keys:
            print('%s %s' % (ip, key))
