# 11. Raspberry Pi (split laptop / Pi 5 setup)

> **Concept**
> - **The work is split by hardware.** The Pi has no GPU suitable for Gazebo or RViz, so the laptop (Ubuntu, ROS 2 Jazzy, Gazebo) runs the sim, `ros_gz_bridge`, twist_mux, RViz and teleop. The Pi 5 gets the CPU-side work: slam_toolbox (localization) and Nav2, started by `launch/pi.launch.py`.
> - **DDS discovery is automatic.** ROS 2 nodes on both machines find each other with no extra configuration when they share a `ROS_DOMAIN_ID` (26 here) on the same network. Here the network is one ethernet cable.
> - **The Pi runs on sim time.** `/clock` is bridged on the laptop and crosses the cable like any other topic, so the Pi's nodes (`use_sim_time: true`) follow the sim. No clock sync between the machines is needed for the sim.
> - **Ubuntu Server 24.04 64-bit, not Raspberry Pi OS.** 24.04 (noble) is Jazzy's tier-1 platform; Raspberry Pi OS has no Jazzy binaries.
> - **`ros-base` on the Pi.** No GUI packages; nothing graphical runs there.

## What was done, by phase
1. **Hardware.** A Pi 5 needs a 5V/5A (27 W) USB-C PD supply and a cable rated for it. A weaker supply browns out at boot (see Troubleshooting). microSD 32 GB or larger. One ethernet cable straight from the Pi to the laptop.
2. **Flash.** Ubuntu Server 24.04 LTS 64-bit with Raspberry Pi Imager (`sudo apt install rpi-imager`). In OS customisation set the hostname (e.g. `shasraspi`), user and password, enable SSH, and optionally Wi-Fi. The first boot runs cloud-init and takes a few minutes.
3. **Share the laptop's connection over the cable.** NetworkManager's shared mode runs a DHCP server and NAT on the interface; the laptop gets `10.42.0.1/24`.
   ```bash
   nmcli device                                    # find the ethernet interface, e.g. enp2s0
   nmcli con add type ethernet ifname enp2s0 con-name pi-link ipv4.method shared
   nmcli con up pi-link
   ip addr show enp2s0                             # expect inet 10.42.0.1/24 and LOWER_UP (no NO-CARRIER)
   ```
4. **Find the Pi and SSH in.** The dnsmasq lease file (`/var/lib/NetworkManager/dnsmasq-*.leases`) may not exist, so don't rely on it.
   ```bash
   ip neigh show dev enp2s0
   sudo apt install -y nmap && nmap -sn 10.42.0.0/24
   ssh <user>@10.42.0.<x>
   ping -c 3 google.com                            # on the Pi; confirms NAT internet through the laptop
   ```
   If the Pi also joined Wi-Fi it can show up with a second address (same MAC).
5. **Fix the apt sources.** The image's `/etc/apt/sources.list.d/ubuntu.sources` listed only `noble` and `noble-security`, but the image shipped packages from `noble-updates`. The `sed` only touches a `Suites:` line that is exactly `noble` (security in its own block) or `noble noble-security` (one block), so a separate security block is left alone:
   ```bash
   cat /etc/apt/sources.list.d/ubuntu.sources
   sudo sed -i -e 's/^Suites: noble$/Suites: noble noble-updates noble-backports/' \
     -e 's/^Suites: noble noble-security$/Suites: noble noble-updates noble-backports noble-security/' \
     /etc/apt/sources.list.d/ubuntu.sources
   ```
   Make sure `Components:` includes `universe`. Then:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y chrony
   sudo reboot
   ```
6. **ROS 2 Jazzy** (official `ros-apt-source` method):
   ```bash
   sudo apt install -y software-properties-common curl
   sudo add-apt-repository universe
   export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
   curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"
   sudo dpkg -i /tmp/ros2-apt-source.deb
   sudo apt update
   sudo apt install -y ros-jazzy-ros-base ros-dev-tools
   echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
   echo "export ROS_DOMAIN_ID=26" >> ~/.bashrc
   ```
   `ROS_DOMAIN_ID=26` must also be set on the laptop.
7. **Cross-machine test.** Pi `ros2 run demo_nodes_cpp talker`, laptop `ros2 run demo_nodes_cpp listener`. The laptop should print "I heard".
8. **Project on the Pi.** Don't use `rosdep install` for this package: `package.xml` pulls `ros_gz_sim`, `rviz2` and `joint_state_publisher_gui`, which are Gazebo/GUI the Pi doesn't need. Install by name:
   ```bash
   sudo apt install -y ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox ros-jazzy-twist-mux ros-jazzy-robot-state-publisher ros-jazzy-xacro
   git clone --depth 1 https://github.com/shass27/eternal_bot_26.git ~/eternal_bot_26
   cd ~/eternal_bot_26 && colcon build --symlink-install --packages-select eternal_bot_description
   echo "source ~/eternal_bot_26/install/setup.bash" >> ~/.bashrc
   ```
   `maps/*.posegraph` is about 7 MB and is needed: `pi.launch.py` loads `obs_map2_serial`. It also rewrites slam_toolbox's `map_file_name` to the installed map, because `config/mapper_params_online_async.yaml` hardcodes `/home/parallels/...`.

## What runs where
| Machine | Installs | Runs |
|---|---|---|
| Laptop | Full desktop Jazzy, Gazebo Harmonic, `ros_gz` | Gazebo, `ros_gz_bridge` (incl. `/clock`), twist_mux, `nonzero_filter`, RViz, teleop |
| Pi 5 | `ros-base`, Nav2, slam_toolbox, twist_mux, robot_state_publisher, xacro | slam_toolbox (localization) + Nav2 via `pi.launch.py` |

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| Pi turns on for a few seconds then off; ethernet LEDs never light | Under-powered USB-C supply or cable (brownout) | 5V/5A PD supply and a rated cable. Test: boot with no SD card; if it still cuts out, it is power. |
| Solid red LED; ethernet lights go off briefly during first boot | cloud-init restarting networking | Wait 3-5 min. |
| `cat: /var/lib/NetworkManager/dnsmasq-*.leases: No such file` | No lease file written, or the shared connection is not up | `nmcli device` should show `pi-link` connected; find the Pi with `ip neigh` / `nmap`. |
| `liblz4-dev : Depends: liblz4-1 (= 1.9.4-1build1) but 1.9.4-1build1.1 is to be installed` (same for `libzstd-dev`) when installing ROS | `noble-updates` missing from the apt sources; the installed libs came from it, so the matching `-dev` is not visible (`apt-cache policy liblz4-dev` shows only noble/main) | Add `noble-updates` (phase 5). |
| slam_toolbox `serialization::Read: Failed to open requested file: /home/parallels/.../obs_map2_serial` | Hardcoded map path in `mapper_params_online_async.yaml` | Use `pi.launch.py`, which rewrites the path. Don't hand-edit. |
| `Couldn't parse params file ... Error parsing a event near line 30` | YAML corrupted by a hand edit in nano (here a pasted command on the `map_file_name` line and two keys merged onto one line; tabs also break YAML) | `git checkout src/eternal_bot_description/config/mapper_params_online_async.yaml`. Inspect with `cat -A`; validate with `python3 -c "import yaml; yaml.safe_load(open('...'))"`. |
| RViz on the laptop shows only the grid | `rviz2 -d src/eternal_bot_description/config/gazebo.rviz` run from home; the relative path doesn't exist, so RViz opens an empty config | Run from the repo root, or `make rviz`. |
| Gazebo Entity Tree shows `eternal_bot` and `eternal_bot_0` | Launch ran twice, or a leftover gz process | `make clean` (or `pkill -9 -f "[g]z sim"`), start once, wait for a single model. |
| Laptop listener hears nothing / Pi sees no topics | `ROS_DOMAIN_ID` differs, `ROS_LOCALHOST_ONLY=1`, ufw blocking, or DDS using another interface (laptop has Wi-Fi, `docker0` and the cable; the Pi may have Wi-Fi + eth) | `echo $ROS_DOMAIN_ID $ROS_LOCALHOST_ONLY`, `sudo ufw status`, `ros2 topic list`. Disabling the Pi's Wi-Fi isolates the cable. |
| `ros2 topic list` works but `ros2 topic hz /scan` hangs | Same multi-interface DDS issue: discovery succeeds, data goes out the wrong interface | As above. |

Launch order for both machines is in the top-level README, [Running on a Raspberry Pi](../README.md#running-on-a-raspberry-pi); the Pi side is `launch/pi.launch.py`.
