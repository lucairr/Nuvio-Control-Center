"""Initialize configuration in container or another no-systemd deployment.
This command NEVER installs to or contacts a TV.
"""
import argparse
import ipaddress
from . import core


def main():
    parser = argparse.ArgumentParser(description='Initialize Nuvio Control Center configuration')
    parser.add_argument('--tv-ip', required=True, help='LG Developer Mode IPv4 address')
    parser.add_argument('--tv-device', default='nuvio-lg')
    parser.add_argument('--tv-name', default='LG webOS TV')
    parser.add_argument('--web-bind', default='0.0.0.0', choices=('127.0.0.1','0.0.0.0'))
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    ipaddress.IPv4Address(args.tv_ip)
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', args.tv_device):
        parser.error('Invalid device alias')
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be 1024 to 65535')
    if core.CONFIG_FILE.exists():
        print('Existing config.json preserved; nothing overwritten.')
        return
    core.write_json(core.CONFIG_FILE, {'tv_ip':args.tv_ip, 'tv_device':args.tv_device,
        'tv_name':args.tv_name[:90], 'auto_update':False,
        'web_bind':args.web_bind, 'web_port':args.port})
    print('Created private configuration. Automatic installation: OFF.')

if __name__ == '__main__':
    main()
