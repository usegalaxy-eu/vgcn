#!/bin/bash
# Remove vggp images that are not currently in use.
openstack image list -c ID -c Name | grep vggp | awk '{print $2}' | xargs openstack image delete
