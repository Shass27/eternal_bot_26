SHELL := /bin/bash
.DEFAULT_GOAL := help

PKG   := eternal_bot_description
CFG   := src/$(PKG)/config
WORLD ?= arena
GUI   ?= True
# each recipe line is its own shell, so source the workspace in front of it
ROS   := source install/setup.bash &&
LAUNCH := $(ROS) ros2 launch $(PKG)

.PHONY: help build sim sim-min slam nav rviz teleop teleop-raw display view clean \
        estop estop-release stop nav-test echo-cmd mux-info

help: ## list targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'
	@echo; echo "vars: WORLD=arena|arena_obs|empty (sim), GUI=True|False (display)"

build: ## colcon build --symlink-install
	colcon build --symlink-install

sim: ## Gazebo sim + bridge + twist_mux (WORLD=...)
	$(LAUNCH) gazebo.launch.py world:=$(WORLD)

sim-min: ## robot in empty world only, raw /cmd_vel
	$(LAUNCH) gazebo_min.launch.py

slam: ## slam_toolbox on a running sim
	$(LAUNCH) slam.launch.py

nav: ## Nav2 (needs sim + slam)
	$(LAUNCH) nav.launch.py

rviz: ## RViz with sim time
	$(ROS) rviz2 -d $(CFG)/gazebo.rviz --ros-args -p use_sim_time:=true

teleop: ## keyboard drive via twist_mux
	$(ROS) ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false

teleop-raw: ## keyboard straight to /cmd_vel (from-scratch SLAM run, no mux/e-stop)
	$(ROS) ros2 run key_teleop key_teleop --ros-args -p twist_stamped_enabled:=false -r key_vel:=cmd_vel

display: ## RViz + joint GUI, no sim (GUI=False to hide GUI)
	$(LAUNCH) display.launch.py gui:=$(GUI)

view: ## urdf-viz preview, no ROS
	./src/$(PKG)/view.sh

estop: ## engage e-stop lock (Ctrl+C, then make estop-release)
	$(ROS) ros2 topic pub -r 10 /e_stop std_msgs/msg/Bool '{data: true}'

estop-release: ## release e-stop lock
	$(ROS) ros2 topic pub --once /e_stop std_msgs/msg/Bool '{data: false}'

stop: ## zero Twist on cmd_vel_emergency (top priority)
	$(ROS) ros2 topic pub -r 10 /cmd_vel_emergency geometry_msgs/msg/Twist '{}'

nav-test: ## 0.1 m/s on cmd_vel_safe (nav priority; keys override)
	$(ROS) ros2 topic pub -r 10 /cmd_vel_safe geometry_msgs/msg/Twist '{linear: {x: 0.1}}'

echo-cmd: ## watch twist_mux output linear.x
	$(ROS) ros2 topic echo /cmd_vel --field linear.x

mux-info: ## who publishes /cmd_vel (only twist_mux should)
	$(ROS) ros2 topic info /cmd_vel -v

clean: ## kill leftover sim processes
	-pkill -9 -f "[g]z sim"
	-pkill -f "[p]arameter_bridge"
	-pkill -f "[r]obot_state_publisher"
	-pkill -f "[t]wist_mux"
	-pkill -f "[n]onzero_filter"
	-pkill -f "[g]azebo.launch"
	-pgrep -fa "[g]z sim"
