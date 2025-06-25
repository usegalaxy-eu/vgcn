#!/bin/bash

# script to repack a qcow2 image to the used size within its filesystem
# will need nbd and qemu-nbd to function

if [ "$#" -ne 2 ]; then
	echo "Usage: $0 <qcow_path> <fs_label>"
	exit 1
fi

if [ ! -f "$1" ]; then
	echo "Given file '$1' is not a file."
	exit 1
fi

if ! lsmod | grep -q nbd; then
	echo "Requires nbd loaded!"
	exit 1
fi

# helper
nbd_find_free() {
	local id=0
	local max=20
	while [ "$(cat /sys/block/nbd${id}/size)" != "0" ] && [ "$id" != "20" ]; do
		(( id ++ ))
	done
	if [ "$id" != "$max" ]; then
		echo "/dev/nbd${id}"
	fi
}

# mount_qcow <container> <partnum> <path>
mount_qcow() {
	[ "$#" -lt 2 ] && exit 1
	[ ! -f "$1" ] && exit 1
	local partnum="$2"
	[ -z "$partnum" ] && exit 1
	local target_path="$3"
	[ ! -d "$target_path" ] && mkdir -p "$target_path"
	local target_nbd="$(nbd_find_free)"
	qemu-nbd -c "$target_nbd" "$1"
	if [ ! -b "${target_nbd}p${partnum}" ]; then
		sleep 1
		if [ ! -b "${target_nbd}p${partnum}" ]; then
			echo "Could not detect newly connected qcow image."
			qemu-nbd -d "$target_nbd"
			return 1
		fi
	fi
	if ! mount "${target_nbd}p${partnum}" "$target_path"; then
		qemu-nbd -d "$target_nbd"
		return 1
	fi
}

# qcow2_used_blocks <container> <partition>
qcow2_used_blocks() {
	local container="$1"
	local part="$2"
	local data="$(mktemp)"
	guestfish -a "$1" -m "${part}:/" --ro statvfs / > "$data"
	read -r bsize blocks bavail bfree rest < <(awk -v OFS=' ' '
		BEGIN { bsize=0; blocks=0; bavail=0 }
		$1 ~ /^bsize:/  { bsize=$2 }
		$1 ~ /^blocks:/ { blocks=$2 }
		$1 ~ /^bavail:/ { bavail=$2 }
		$1 ~ /^bfree:/  { bfree=$2 }
	  END {print bsize, blocks, bavail, bfree}
	' "$data")
	rm -f "$data"
	echo "$(( ( blocks - bfree ) * ( bsize / 1024 ) ))" # in KB
}

################################################################################
## MAIN
##
declare -g partname="$(guestfish -a "$1" --ro run : findfs-label "$2")"
[ -z "$partname" ] && exit 1
echo "## Using partition: $partname"
used_kb="$(qcow2_used_blocks "$1" "$partname")"

echo "## Used space: $used_kb"
shrink_container="${1##*/}.shrinked"
[ -e "$shrink_container" ] && rm -f $shrink_container

echo "## Creating target: $shrink_container"

guestfish << EOF
disk-create $shrink_container qcow2 $(( used_kb + ( used_kb / 20 ) + ( 1024 * 500 ) ))K
add $shrink_container
run
part-disk /dev/sda gpt
part-set-name /dev/sda 1 $2
mkfs xfs /dev/sda1
EOF
if [ "$?" -ne 0 ]; then
	echo "Error creating destination container."
	exit 1
fi

echo "## Mounting: $1"
mount_qcow "$1" "${partname: -1}" "shrink_source"
echo "## Mounting: $shrink_container"
mount_qcow "$shrink_container" "1" "shrink_dest"

echo "## Rsync'ing..."
rsync -aAX "shrink_source/" "shrink_dest"
sync

echo "## Cleaning up destination..."
# cleanup dest qcow2

echo "## Cleaning up ..."

umount "shrink_source"
umount "shrink_dest"

qemu-nbd -d /dev/nbd0
qemu-nbd -d /dev/nbd1

echo "## Sparsify'ing..."

export LIBGUESTFS_DEBUG=1 LIBGUESTFS_TRACE=1
TMPDIR=$(pwd)/tmp virt-sparsify --compress "$shrink_container" "${1}.minified"

echo "Done!"
exit 0
