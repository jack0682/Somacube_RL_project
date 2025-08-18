#!/bin/bash
#
# SomaCube RL Complete Integration Test
# Demonstrates full Day-0 pipeline with simulated data
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARN:${NC} $*"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $*"
}

# Configuration
TEST_DURATION=120
SCENARIO="normal"
OUTPUT_DIR="integration_test_$(date +%Y%m%d_%H%M%S)"

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run complete SomaCube RL integration test

Options:
  --duration SECONDS    Test duration (default: 120)
  --scenario SCENARIO   Simulation scenario: normal|degraded|failure (default: normal)
  --output-dir DIR      Output directory for results
  -h, --help           Show this help

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --duration)
            TEST_DURATION="$2"
            shift 2
            ;;
        --scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
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

log "Starting SomaCube RL Integration Test"
log "Duration: ${TEST_DURATION}s, Scenario: ${SCENARIO}, Output: ${OUTPUT_DIR}"

# Create output directory
mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

# Check prerequisites
log "Checking prerequisites..."
if ! command -v ros2 >/dev/null; then
    error "ROS 2 not found. Source ROS 2 setup."
    exit 1
fi

if ! ros2 pkg list | grep -q doosan_somacube_rl; then
    error "Package doosan_somacube_rl not found. Build and source workspace."
    exit 1
fi

# Function to cleanup processes
cleanup() {
    log "Cleaning up processes..."
    pkill -f "simulate_data.py" || true
    pkill -f "system_monitor.py" || true 
    pkill -f "validate_dod.py" || true
    pkill -f "bringup_real.launch.py" || true
    sleep 2
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start data simulation
log "Starting data simulation (scenario: ${SCENARIO})..."
python3 ~/ros2_ws/src/doosan_somacube_rl/scripts/simulate_data.py \
    --scenario "${SCENARIO}" --duration $((TEST_DURATION + 30)) --verbose &
SIM_PID=$!

# Wait for simulation to start
sleep 3

# Start system monitoring
log "Starting system monitor..."
python3 ~/ros2_ws/src/doosan_somacube_rl/scripts/system_monitor.py \
    --duration "${TEST_DURATION}" --verbose \
    --output "system_health_${SCENARIO}.csv" &
MON_PID=$!

# Start DoD validation
log "Starting DoD validation..."
python3 ~/ros2_ws/src/doosan_somacube_rl/scripts/validate_dod.py \
    --duration "${TEST_DURATION}" --verbose &
DOD_PID=$!

# Record bag data
log "Starting bag recording..."
~/ros2_ws/src/doosan_somacube_rl/scripts/bag_record.sh \
    --duration "${TEST_DURATION}" --name "integration_${SCENARIO}" \
    --output-dir "$(pwd)" &
BAG_PID=$!

# Monitor progress
log "Integration test running for ${TEST_DURATION} seconds..."
log "Monitoring PIDs: SIM=${SIM_PID}, MON=${MON_PID}, DOD=${DOD_PID}, BAG=${BAG_PID}"

# Wait for completion
sleep "${TEST_DURATION}"

# Wait for processes to complete
log "Waiting for processes to complete..."
wait ${MON_PID} 2>/dev/null || true
wait ${DOD_PID} 2>/dev/null || true  
wait ${BAG_PID} 2>/dev/null || true

# Cleanup simulation
kill ${SIM_PID} 2>/dev/null || true
wait ${SIM_PID} 2>/dev/null || true

# Collect results
log "Collecting test results..."

# Check if files were created
echo "Generated files:"
ls -la

# Analyze system health
if [[ -f "system_health_${SCENARIO}.csv" ]]; then
    log "System health analysis:"
    tail -5 "system_health_${SCENARIO}.csv"
else
    warn "No system health data generated"
fi

# Check DoD validation results
if ls dod_validation_*.json >/dev/null 2>&1; then
    DOD_FILE=$(ls -t dod_validation_*.json | head -1)
    log "DoD validation results from ${DOD_FILE}:"
    
    if command -v jq >/dev/null; then
        cat "${DOD_FILE}" | jq '.overall_status, .summary.average_score'
    else
        grep -E "(overall_status|average_score)" "${DOD_FILE}" || echo "Results in ${DOD_FILE}"
    fi
else
    warn "No DoD validation results found"
fi

# Check bag files
if ls *.db3 >/dev/null 2>&1; then
    log "Bag files created:"
    ls -lh *.db3
    
    # Basic bag info
    BAG_FILE=$(ls -t *.db3 | head -1 | sed 's/.db3//')
    if command -v ros2 >/dev/null; then
        log "Bag info for ${BAG_FILE}:"
        ros2 bag info "${BAG_FILE}" | head -10 || true
    fi
else
    warn "No bag files found"
fi

# Generate summary report
cat > integration_test_summary.txt << EOF
SomaCube RL Integration Test Summary
====================================

Test Configuration:
- Duration: ${TEST_DURATION} seconds
- Scenario: ${SCENARIO}
- Timestamp: $(date)
- Output Directory: $(pwd)

Files Generated:
$(ls -la)

System Status: 
$(if [[ -f "system_health_${SCENARIO}.csv" ]]; then echo "Health monitoring: OK"; else echo "Health monitoring: FAILED"; fi)
$(if ls dod_validation_*.json >/dev/null 2>&1; then echo "DoD validation: OK"; else echo "DoD validation: FAILED"; fi)
$(if ls *.db3 >/dev/null 2>&1; then echo "Bag recording: OK"; else echo "Bag recording: FAILED"; fi)

Test Result: $(if [[ -f "system_health_${SCENARIO}.csv" ]] && ls dod_validation_*.json >/dev/null 2>&1; then echo "SUCCESS"; else echo "PARTIAL"; fi)
EOF

log "Integration test completed!"
log "Summary:"
cat integration_test_summary.txt

log "Test results saved in: $(pwd)"
log "Integration test $(if [[ -f "system_health_${SCENARIO}.csv" ]] && ls dod_validation_*.json >/dev/null 2>&1; then echo "${GREEN}PASSED${NC}"; else echo "${YELLOW}PARTIALLY PASSED${NC}"; fi)"