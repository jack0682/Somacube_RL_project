#!/bin/bash

# SomaCube RL Data Collection Script
# Records all essential topics to ROS2 bag files for analysis and training data

set -e  # Exit on any error

# Script configuration
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default parameters
DEFAULT_DURATION=300  # 5 minutes
DEFAULT_OUTPUT_DIR="$HOME/somacube_bags"
DEFAULT_BAG_NAME="somacube_$(date +%Y%m%d_%H%M%S)"
DEFAULT_COMPRESSION="zstd"

# Parse command line arguments
DURATION=$DEFAULT_DURATION
OUTPUT_DIR=$DEFAULT_OUTPUT_DIR
BAG_NAME=$DEFAULT_BAG_NAME
COMPRESSION=$DEFAULT_COMPRESSION
VERBOSE=false
DRY_RUN=false

usage() {
    echo "Usage: $SCRIPT_NAME [OPTIONS]"
    echo ""
    echo "Records SomaCube RL system topics to ROS2 bag files"
    echo ""
    echo "Options:"
    echo "  -d, --duration SECONDS    Recording duration in seconds (default: $DEFAULT_DURATION)"
    echo "  -o, --output-dir DIR      Output directory for bag files (default: $DEFAULT_OUTPUT_DIR)"
    echo "  -n, --name NAME           Bag name prefix (default: somacube_TIMESTAMP)"
    echo "  -c, --compression TYPE    Compression type: none, zstd, lz4 (default: $DEFAULT_COMPRESSION)"
    echo "  -v, --verbose             Enable verbose output"
    echo "  --dry-run                 Show commands without executing"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $SCRIPT_NAME                        # Record for 5 minutes with defaults"
    echo "  $SCRIPT_NAME -d 600 -n experiment1  # Record for 10 minutes with custom name"
    echo "  $SCRIPT_NAME --dry-run              # Show what would be recorded"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -n|--name)
            BAG_NAME="$2"
            shift 2
            ;;
        -c|--compression)
            COMPRESSION="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate compression type
case $COMPRESSION in
    none|zstd|lz4)
        ;;
    *)
        echo "Error: Invalid compression type '$COMPRESSION'. Use: none, zstd, lz4"
        exit 1
        ;;
esac

# Define topics to record
# Essential system topics for RL training and analysis
TOPICS=(
    # Vision and sensing
    "/camera/color/image_raw"
    "/camera/aligned_depth_to_color/image_raw" 
    "/camera/color/camera_info"
    "/ee/ft"
    
    # Point cloud processing
    "/pc_preprocess/output"
    "/debug/heightmap"
    
    # Registration and pose tracking
    "/pc_register/pose"
    "/pc_register/quality"
    "/pose_tracker/smoothed_pose"
    
    # Control and policy
    "/layer1_manager/target_pose"
    "/policy/lo/cmd"
    "/doosan/cmd_vel"
    "/imp_ctrl/confidence"
    
    # Safety monitoring
    "/safety/events"
    "/safety/status"
    "/safety/emergency_stop"
    
    # Sequencing and assembly
    "/sequencer/state" 
    "/sequencer/stage_complete"
    "/layer1_manager/current_piece"
    "/layer1_manager/assembly_status"
    
    # Logging and metrics
    "/logger/kpi_metrics"
    "/logger/success_rate"
    "/logger/system_health"
    
    # Policy/RL specific
    "/policy/reward"
    "/policy/confidence" 
    "/policy/observation_norm"
    
    # System state
    "/joint_states"
    "/tf"
    "/tf_static"
)

# High-frequency debug topics (optional, recorded separately)
DEBUG_TOPICS=(
    "/pc_register/debug/correspondences"
    "/pose_tracker/debug/outliers" 
    "/imp_ctrl/debug/forces"
    "/safety/debug/violations"
)

# Function to check if ROS2 is running
check_ros2() {
    if ! command -v ros2 &> /dev/null; then
        echo "Error: ROS2 not found. Please source ROS2 setup."
        exit 1
    fi
    
    # Check if ros2 daemon is running
    if ! ros2 daemon status &> /dev/null; then
        echo "Warning: ROS2 daemon not running. Starting daemon..."
        ros2 daemon start
        sleep 2
    fi
}

# Function to check topic availability
check_topics() {
    local missing_topics=()
    local available_topics
    
    echo "Checking topic availability..."
    available_topics=$(ros2 topic list 2>/dev/null || echo "")
    
    for topic in "${TOPICS[@]}"; do
        if [[ ! "$available_topics" =~ $topic ]]; then
            missing_topics+=("$topic")
        fi
    done
    
    if [[ ${#missing_topics[@]} -gt 0 ]]; then
        echo "Warning: The following topics are not available:"
        printf '  %s\n' "${missing_topics[@]}"
        echo ""
        echo "This may indicate that some nodes are not running."
        echo "Continue anyway? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    else
        echo "✓ All essential topics are available"
    fi
}

# Function to create output directory
setup_output_dir() {
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        echo "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi
    
    # Check write permissions
    if [[ ! -w "$OUTPUT_DIR" ]]; then
        echo "Error: Cannot write to output directory: $OUTPUT_DIR"
        exit 1
    fi
}

# Function to build ros2 bag record command
build_record_command() {
    local cmd="ros2 bag record"
    
    # Add compression
    if [[ "$COMPRESSION" != "none" ]]; then
        cmd="$cmd --compression-mode file --compression-format $COMPRESSION"
    fi
    
    # Add output options
    cmd="$cmd --output $OUTPUT_DIR/$BAG_NAME"
    
    # Add max bag size to prevent huge files (1GB)
    cmd="$cmd --max-bag-size 1073741824"  # 1GB in bytes
    
    # Add topics
    for topic in "${TOPICS[@]}"; do
        cmd="$cmd $topic"
    done
    
    echo "$cmd"
}

# Function to start system health monitoring
start_health_monitor() {
    local monitor_log="$OUTPUT_DIR/${BAG_NAME}_health.log"
    
    echo "Starting system health monitoring..."
    echo "Health monitor log: $monitor_log"
    
    # Start topic verification in background
    (
        echo "=== System Health Monitor Started: $(date) ===" > "$monitor_log"
        echo "Bag recording duration: ${DURATION}s" >> "$monitor_log"
        echo "Topics being recorded: ${#TOPICS[@]}" >> "$monitor_log"
        echo "" >> "$monitor_log"
        
        # Run topic verification for the recording duration
        cd "$PROJECT_DIR/scripts"
        python3 verify_topics.py --duration "$DURATION" --quiet >> "$monitor_log" 2>&1
        
        echo "" >> "$monitor_log"
        echo "=== System Health Monitor Completed: $(date) ===" >> "$monitor_log"
    ) &
    
    local monitor_pid=$!
    echo "Health monitor PID: $monitor_pid"
    return $monitor_pid
}

# Function to record metadata
record_metadata() {
    local metadata_file="$OUTPUT_DIR/${BAG_NAME}_metadata.json"
    
    echo "Recording session metadata..."
    
    cat > "$metadata_file" << EOF
{
    "session_info": {
        "timestamp": "$(date -Iseconds)",
        "duration_seconds": $DURATION,
        "bag_name": "$BAG_NAME",
        "compression": "$COMPRESSION",
        "output_directory": "$OUTPUT_DIR"
    },
    "system_info": {
        "hostname": "$(hostname)",
        "user": "$(whoami)",
        "ros_distro": "${ROS_DISTRO:-unknown}",
        "workspace": "$PROJECT_DIR"
    },
    "topics_recorded": $(printf '%s\n' "${TOPICS[@]}" | jq -R . | jq -s .),
    "recording_command": "$(build_record_command)",
    "git_info": {
        "branch": "$(cd "$PROJECT_DIR" && git branch --show-current 2>/dev/null || echo 'unknown')",
        "commit": "$(cd "$PROJECT_DIR" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
        "dirty": $(cd "$PROJECT_DIR" && [[ -n "$(git status --porcelain 2>/dev/null)" ]] && echo "true" || echo "false")
    }
}
EOF
    
    echo "Metadata saved: $metadata_file"
}

# Function to display recording progress
show_progress() {
    local start_time=$(date +%s)
    local end_time=$((start_time + DURATION))
    
    echo "Recording in progress..."
    echo "Press Ctrl+C to stop early"
    echo ""
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        local remaining=$((DURATION - elapsed))
        local progress=$((elapsed * 100 / DURATION))
        
        printf "\rProgress: [%3d%%] %3d/%3d seconds remaining: %3d" \
               "$progress" "$elapsed" "$DURATION" "$remaining"
        
        sleep 1
    done
    
    echo ""
    echo "Recording duration completed."
}

# Function to display final summary
show_summary() {
    local bag_path="$OUTPUT_DIR/$BAG_NAME"
    
    echo ""
    echo "=== RECORDING SUMMARY ==="
    echo "Bag name: $BAG_NAME"
    echo "Output directory: $OUTPUT_DIR"
    echo "Duration: ${DURATION}s"
    echo "Compression: $COMPRESSION"
    echo ""
    
    if [[ -d "$bag_path" ]]; then
        echo "Bag file info:"
        ros2 bag info "$bag_path" 2>/dev/null || echo "Could not read bag info"
        
        # Show disk usage
        local bag_size=$(du -sh "$bag_path" 2>/dev/null | cut -f1)
        echo "Bag size: $bag_size"
    fi
    
    echo ""
    echo "Files created:"
    echo "  Bag: $bag_path"
    echo "  Metadata: ${bag_path}_metadata.json"
    echo "  Health log: ${bag_path}_health.log"
    echo ""
    echo "To replay the bag:"
    echo "  ros2 bag play $bag_path"
    echo ""
    echo "To analyze topics:"
    echo "  ros2 bag info $bag_path"
    echo "  python3 scripts/analyze_bag.py $bag_path"
}

# Main execution function
main() {
    echo "SomaCube RL Data Collection"
    echo "=========================="
    echo "Duration: ${DURATION}s"
    echo "Output: $OUTPUT_DIR/$BAG_NAME"
    echo "Compression: $COMPRESSION"
    echo "Topics: ${#TOPICS[@]}"
    echo ""
    
    # Pre-flight checks
    check_ros2
    setup_output_dir
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Topics to record:"
        printf '  %s\n' "${TOPICS[@]}"
        echo ""
    fi
    
    check_topics
    
    # Record metadata
    record_metadata
    
    # Build command
    local record_cmd
    record_cmd=$(build_record_command)
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY RUN - Would execute:"
        echo "$record_cmd"
        echo ""
        echo "Duration: ${DURATION}s"
        exit 0
    fi
    
    echo "Starting recording..."
    echo "Command: $record_cmd"
    echo ""
    
    # Start health monitoring
    start_health_monitor
    local monitor_pid=$?
    
    # Start recording with timeout
    if [[ "$VERBOSE" == "true" ]]; then
        timeout "$DURATION" $record_cmd &
    else
        timeout "$DURATION" $record_cmd > /dev/null 2>&1 &
    fi
    
    local record_pid=$!
    
    # Show progress
    show_progress &
    local progress_pid=$!
    
    # Wait for recording to complete
    wait $record_pid 2>/dev/null
    local record_exit_code=$?
    
    # Clean up progress display
    kill $progress_pid 2>/dev/null || true
    wait $progress_pid 2>/dev/null || true
    
    # Wait for health monitor
    wait $monitor_pid 2>/dev/null || true
    
    echo ""
    if [[ $record_exit_code -eq 0 || $record_exit_code -eq 124 ]]; then
        echo "✓ Recording completed successfully"
    else
        echo "⚠ Recording ended with exit code: $record_exit_code"
    fi
    
    show_summary
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n\nRecording interrupted by user"; exit 130' INT

# Run main function
main "$@"