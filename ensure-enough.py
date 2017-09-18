import os
from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient import client as nova_client
from glanceclient import client as glance_client
loader = loading.get_plugin_loader('password')
auth = loader.load_from_options(auth_url=os.environ['OS_AUTH_URL'],
                                username=os.environ['OS_USERNAME'],
                                password=os.environ['OS_PASSWORD'],
                                project_id=os.environ['OS_TENANT_ID'])
sess = session.Session(auth=auth)
nova = nova_client.Client('2.0', session=sess)
glance = glance_client.Client('2', session=sess)

CURRENT_IMAGE_NAME = 'vgcnbwc7-21'
DESIRED_IMAGE_COUNT = 12

# Everything below here is probably fine to be hard-coded.
CURRENT_IMAGE = [image for image in glance.images.list() if image.name == CURRENT_IMAGE_NAME][0]
FLAVOR = [flavor for flavor in nova.flavors.list() if flavor.name == 'c.c10m55'][0]
SSHKEY = 'cloud2'
NETWORK = [network for network in nova.networks.list() if network.human_id == 'galaxy-net'][0]
SECGROUPS = 'ufr-only-v2'
TO_REMOVE = []

current_count = 0
previously_used_max_id = 0
for server in nova.servers.list():
	if server.name.startswith('vgcnbwc'):
		server_id_num = int(server.name[len('vgcnbwc-'):])
		if server_id_num > previously_used_max_id:
			previously_used_max_id = server_id_num
		
		server_image_name = glance.images.get(server.image['id'])['name']
		if server_image_name != CURRENT_IMAGE_NAME:
			TO_REMOVE.append(server)
		else:
			current_count += 1

if current_count < DESIRED_IMAGE_COUNT:
	for idx in range(previously_used_max_id + 1, DESIRED_IMAGE_COUNT + 1):
		print(nova.servers.create(
			name="vgcnbwc-%s" % idx,
			image=CURRENT_IMAGE,
			flavor=FLAVOR,
			key_name=SSHKEY,
			availability_zone='nova',
			nics=[{'net-id': NETWORK.id}],
		))

for server in TO_REMOVE:
	server_ip = server.networks['galaxy-net'][0]
	server_image_name = glance.images.get(server.image['id'])['name']
	print('(TODO) Terminating:', server.name, server.id, server_image_name)
	# TODO: log-in, condor_drain, check for no jobs, then terminate.
