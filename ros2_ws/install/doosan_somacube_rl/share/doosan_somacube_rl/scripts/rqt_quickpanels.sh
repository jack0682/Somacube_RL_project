#!/bin/bash
#
# RQt Quick Panels for SomaCube RL System Monitoring
# Opens pre-configured RQt dashboard for real-time system monitoring
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "${SCRIPT_DIR}")"
RQT_PERSPECTIVE="${PACKAGE_DIR}/config/somacube_monitoring.perspective"

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Launch RQt dashboard with pre-configured panels for SomaCube RL monitoring

Options:
  --profile PROFILE     Load specific monitoring profile [default|debug|minimal]
  --no-perspective      Skip loading custom perspective file
  --list-topics         Show available topics for monitoring
  --create-perspective  Create new perspective file from current layout
  -v, --verbose         Enable verbose output
  -h, --help           Show this help message

Profiles:
  default    - Standard monitoring: quality, forces, KPI, safety events
  debug      - Debug mode: all topics + raw data plots + node graphs  
  minimal    - Minimal: KPI dashboard only
  safety     - Safety focus: forces, events, system health

Examples:
  $(basename "$0")                              # Launch default profile
  $(basename "$0") --profile debug              # Launch with debug panels
  $(basename "$0") --list-topics               # Show monitorable topics
  $(basename "$0") --create-perspective        # Save current layout

EOF
}

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARN:${NC} $*" >&2
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $*" >&2
}

check_dependencies() {
    local missing_deps=()
    
    if ! command -v rqt >/dev/null 2>&1; then
        missing_deps+=("rqt")
    fi
    
    if ! command -v ros2 >/dev/null 2>&1; then
        missing_deps+=("ros2")
    fi
    
    # Check RQt plugins
    local required_plugins=(
        "rqt_plot"
        "rqt_topic" 
        "rqt_console"
        "rqt_graph"
        "rqt_robot_monitor"
    )
    
    for plugin in "${required_plugins[@]}"; do
        if ! ros2 pkg list | grep -q "^${plugin}$"; then
            warn "RQt plugin ${plugin} not found - some panels may not work"
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "Missing dependencies: ${missing_deps[*]}"
        error "Install with: sudo apt install ros-humble-rqt*"
        exit 1
    fi
}

list_topics() {
    log "Available SomaCube RL topics for monitoring:"
    echo
    
    local categories=(
        "Quality Metrics:/pc_register/quality,/pose/filtered"
        "Safety & Forces:/ee/ft,/safety/events,/gripper/state"
        "Control Commands:/policy/lo/cmd,/layer1/next_target"
        "System Health:/kpi/state,/sequencer/state"
        "Debug Data:/debug/pc_raw,/debug/pc_filtered,/debug/heightmap"
    )
    
    for category_line in "${categories[@]}"; do
        local category="${category_line%%:*}"
        local topics="${category_line#*:}"
        
        echo -e "${BLUE}${category}:${NC}"
        IFS=',' read -ra topic_array <<< "$topics"
        for topic in "${topic_array[@]}"; do
            if ros2 topic list 2>/dev/null | grep -q "^${topic}$"; then
                echo -e "  ${GREEN}✓${NC} $topic $(ros2 topic hz "$topic" --window 10 --timeout 2 2>/dev/null || echo '[not publishing]')"
            else
                echo -e "  ${RED}✗${NC} $topic [topic not found]"
            fi
        done
        echo
    done
}

create_perspective() {
    log "Creating perspective file from current RQt layout..."
    
    # Launch RQt and wait for user to set up layout
    cat << EOF

${YELLOW}Instructions:${NC}
1. RQt will open shortly
2. Set up your desired panel layout:
   - Add plots: Plugins > Visualization > Plot
   - Add topic monitor: Plugins > Topics > Topic Monitor  
   - Add console: Plugins > Logging > Console
   - Arrange panels as desired
3. Save perspective: Perspectives > Export perspective
4. Save to: ${RQT_PERSPECTIVE}
5. Close RQt when done

Press Enter to launch RQt...
EOF
    
    read -r
    rqt --perspective-file "${RQT_PERSPECTIVE}" 2>/dev/null || rqt
    
    if [ -f "${RQT_PERSPECTIVE}" ]; then
        log "Perspective saved to: ${RQT_PERSPECTIVE}"
    else
        warn "No perspective file created"
    fi
}

launch_profile() {
    local profile="$1"
    local perspective_arg=""
    
    if [ -f "${RQT_PERSPECTIVE}" ] && [ "$USE_PERSPECTIVE" = true ]; then
        perspective_arg="--perspective-file ${RQT_PERSPECTIVE}"
    fi
    
    log "Launching RQt with profile: ${profile}"
    
    case "$profile" in
        "default")
            launch_default_profile "$perspective_arg"
            ;;
        "debug") 
            launch_debug_profile "$perspective_arg"
            ;;
        "minimal")
            launch_minimal_profile "$perspective_arg"
            ;;
        "safety")
            launch_safety_profile "$perspective_arg"
            ;;
        *)
            error "Unknown profile: $profile"
            exit 1
            ;;
    esac
}

launch_default_profile() {
    local perspective_arg="$1"
    
    log "Starting default monitoring dashboard..."
    
    # Launch main RQt with perspective
    rqt $perspective_arg &
    local rqt_pid=$!
    
    sleep 2
    
    # Launch specific plots in background
    rqt_plot /pc_register/quality/mean_point2plane_m \
             /pc_register/quality/geodesic_deg \
             /pc_register/quality/inlier_ratio --title "Registration Quality" &
    
    rqt_plot /ee/ft/wrench/force/x \
             /ee/ft/wrench/force/y \
             /ee/ft/wrench/force/z --title "Forces" &
             
    rqt_plot /kpi/state --title "System KPIs" &
    
    wait $rqt_pid
}

launch_debug_profile() {
    local perspective_arg="$1"
    
    log "Starting debug monitoring dashboard..."
    
    # Launch comprehensive debug setup
    rqt $perspective_arg &
    sleep 2
    
    # System graphs and diagnostics
    rqt_graph &
    rqt_console &
    rqt_topic &
    
    # All quality metrics
    rqt_plot /pc_register/quality/mean_point2plane_m \
             /pc_register/quality/chamfer_bidir_m \
             /pc_register/quality/inlier_ratio \
             /pc_register/quality/icp_residual_std \
             /pc_register/quality/geodesic_deg --title "Full Quality Metrics" &
    
    # Forces and torques
    rqt_plot /ee/ft/wrench/force/x \
             /ee/ft/wrench/force/y \
             /ee/ft/wrench/force/z \
             /ee/ft/wrench/torque/x \
             /ee/ft/wrench/torque/y \
             /ee/ft/wrench/torque/z --title "Full F/T" &
    
    # Policy commands
    rqt_plot /policy/lo/cmd/dx \
             /policy/lo/cmd/dy \
             /policy/lo/cmd/dz --title "Policy Position Commands" &
    
    rqt_plot /policy/lo/cmd/droll \
             /policy/lo/cmd/dpitch \
             /policy/lo/cmd/dyaw --title "Policy Rotation Commands" &
    
    log "Debug dashboard launched. Close individual windows when done."
}

launch_minimal_profile() {
    local perspective_arg="$1"
    
    log "Starting minimal KPI dashboard..."
    
    # Just KPI monitoring
    rqt_plot /kpi/state --title "SomaCube KPIs" &
    rqt_console &
}

launch_safety_profile() {
    local perspective_arg="$1"
    
    log "Starting safety monitoring dashboard..."
    
    rqt $perspective_arg &
    sleep 2
    
    # Safety-focused plots
    rqt_plot /ee/ft/wrench/force/x \
             /ee/ft/wrench/force/y \
             /ee/ft/wrench/force/z --title "Contact Forces" &
             
    rqt_plot /safety/events --title "Safety Events" &
    rqt_console --filter-severity 3 &  # Warnings and above
    
    # System health
    rqt_plot /kpi/state --title "System Health KPIs" &
}

# Parse command line arguments
PROFILE="default"
USE_PERSPECTIVE=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --no-perspective)
            USE_PERSPECTIVE=false
            shift
            ;;
        --list-topics)
            list_topics
            exit 0
            ;;
        --create-perspective)
            create_perspective
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    if [ "$VERBOSE" = true ]; then
        set -x
    fi
    
    log "SomaCube RL RQt Dashboard Launcher"
    log "Profile: $PROFILE"
    
    check_dependencies
    
    # Ensure ROS 2 is sourced
    if [ -z "${ROS_DISTRO:-}" ]; then
        error "ROS 2 not sourced. Run: source /opt/ros/humble/setup.bash"
        exit 1
    fi
    
    # Check if our package is available
    if ! ros2 pkg list | grep -q "^doosan_somacube_rl$"; then
        error "doosan_somacube_rl package not found. Build and source workspace."
        exit 1
    fi
    
    launch_profile "$PROFILE"
}

# Handle script termination
trap 'log "Shutting down RQt dashboard..."; pkill -f rqt; exit 0' INT TERM

main "$@"