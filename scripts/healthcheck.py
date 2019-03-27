# Script for checking the health of a server.
#
# Example for command-line usage:
# python3 healthcheck.py --ip_addresses 1.1.1.1 8.8.8.8 --mount_points / \
#                        --env_variables PATH --space_checks /,10 --details
#
# 2019, Andreas Skorczyk <me@andreas-sk.de>

import argparse
import os
import subprocess
import sys

from timeout import (TimeoutException,
                     timeout)


class HealthChecker:
    def check_network(self, ip_addresses):
        """
        Checks for a given list of ip-addresses if they are reachable.
        """
        reachable = True

        for ip in ip_addresses:
            # Use normal call of "ping" to check reachability
            with open(os.devnull, 'w') as devnull:
                try:
                    subprocess.check_call(
                        ["ping", "-c", "1", "-W", "2", ip],
                        stdout=devnull,  # suppress output
                        stderr=devnull
                    )
                except subprocess.CalledProcessError:
                    reachable = False

        return reachable

    def check_mount_points(self, mount_points):
        """
        Checks for a given list of mount_points if they are correctly mounted.
        """
        mounted = True

        for mount in mount_points:
            mounted = mounted and os.path.ismount(mount)

            # Use check_disk_space to additionally test if mount is responsive
            mounted = mounted and self.check_disk_space([(mount, 0)])

        return mounted

    def check_files_exist(self, files):
        """
        Checks for a given list of file-paths if they exist.
        """
        exists = True

        for file in files:
            exists = exists and os.path.isfile(files)

        return exists

    def check_disk_space(self, paths, max_wait=5):
        """
        Checks for a given list of (path, min_percent)-tuples,
        if at least min_percent are still available at
        path (e.g. at least 10% free disk space).
        """
        satisfied = True

        for path, min_percent in paths:
            # Use timeout as a hard-mounted disk may still be mounted
            # while not responding, which could cause a infinite wait
            try:
                # Calculate available disk space using statvfs
                stat = timeout(max_wait)(os.statvfs)(path)
                disk_capacity = stat.f_blocks * stat.f_frsize
                free = stat.f_bavail * stat.f_frsize
                free_percentage = 100 - (free / (disk_capacity / 100))

                if free_percentage < min_percent:
                    satisfied = False

            except (OSError, TimeoutException):
                satisfied = False

        return satisfied

    def check_env(self, env_variables):
        """
        Checks for a given list of environment-variables if they are set.
        """
        env_set = True

        for env in env_variables:
            env_set = env_set and env in os.environ

        return env_set


if __name__ == "__main__":
    hc = HealthChecker()
    details = False

    # Parse arguments if given or use default-checks instead
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument("--ip_addresses", nargs="+", type=str,
                            help="1.1.1.1 8.8.8.8")
        parser.add_argument("--mount_points", nargs="+", type=str,
                            help="/ /mount")
        parser.add_argument("--space_checks", nargs="+", type=str,
                            help="/,10 /mount,50")
        parser.add_argument("--env_variables", nargs="+", type=str,
                            help="ENV1 ENV2")
        parser.add_argument("--details", action='store_true')
        args = parser.parse_args()

        ip_addresses = args.ip_addresses or []
        mount_points = args.mount_points or []
        env_variables = args.env_variables or []
        details = args.details

        # Manually parse space_checks
        space_checks = []
        for check in args.space_checks or []:
            path, space = check.split(",")
            space_checks.append((path, int(space)))
    else:
        ip_addresses = ["1.1.1.1"]
        mount_points = ["/data", "/cvmfs"]
        space_checks = [("/data/share", 20)]
        env_variables = []

    network_health = hc.check_network(ip_addresses)
    mount_health = hc.check_mount_points(mount_points)
    disk_space_health = hc.check_disk_space(space_checks)
    env_health = hc.check_env(env_variables)

    healthy = network_health and mount_health and disk_space_health \
        and env_health

    print("NODE_IS_HEALTHY = " + str(healthy))

    if details:
        print("Network: %s, Mounts: %s, Disk Space: %s, Env. Variables: %s" %
              (network_health, mount_health, disk_space_health, env_health))

    if not healthy:
        exit(1)
