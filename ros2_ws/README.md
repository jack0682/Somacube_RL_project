# SOMA Cube Assembly with Reinforcement Learning

Implementation of a complete SOMA cube assembly system using reinforcement learning, based on the paper *"High-Speed Autonomous Robotic Assembly Using In-Hand Manipulation and Re-Grasping"*.

## System Overview

This implementation provides:
- **OpenAI Gym-compatible environment** for SOMA cube assembly
- **PyBullet physics simulation** with UR5e robot and 2-DOF gripper
- **PPO training script** using Stable-Baselines3
- **Re-grasping capability** following the paper's 25% re-grasp strategy
- **Performance targeting** the paper's 95% success rate

## Key Features

### Environment (`soma_cube_gym_env.py`)
- 3D SOMA cube assembly simulation (3×3×3 target)
- 7 distinct SOMA pieces with realistic physics
- Vertical pickup constraint implementation
- Multi-modal observations (RGB-D, poses, occupancy matrix)
- Reward structure: +10 correct placement, +100 completion, -5 collision

### Training (`ppo_soma_trainer.py`)
- PPO implementation optimized for robotic assembly
- Parallel environment training (8 environments default)
- Custom policy networks with attention mechanism
- Comprehensive evaluation and logging
- Tensorboard integration

### Re-grasping (`re_grasp_module.py`)
- Intelligent re-grasping strategies from the paper
- 4 re-grasp types: position, rotation, approach, in-hand manipulation
- 25% re-grasp rate matching paper results
- Success rate tracking per strategy

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install PyBullet (if needed)
pip install pybullet

# For CUDA support (optional)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Usage

### Training

```bash
# Basic training (1M timesteps, 8 parallel environments)
python ppo_soma_trainer.py --experiment-name soma_training_v1

# Custom configuration
python ppo_soma_trainer.py \
  --experiment-name custom_training \
  --timesteps 2000000 \
  --n-envs 16 \
  --learning-rate 1e-4 \
  --device cuda

# Training without re-grasping
python ppo_soma_trainer.py --no-re-grasp --experiment-name no_regrasp_baseline
```

### Evaluation Only

```bash
# Evaluate existing model
python ppo_soma_trainer.py --eval-only models/soma_training_v1/final_model.zip
```

### Environment Testing

```bash
# Test environment directly
python soma_cube_gym_env.py
```

## Configuration

### Training Parameters
- **Learning Rate**: 3e-4 (optimized for robotic assembly)
- **Batch Size**: 64
- **N Steps**: 2048 (rollout length)
- **Parallel Environments**: 8
- **Total Timesteps**: 1M (adjustable)

### Environment Parameters
- **Max Episode Steps**: 500
- **Re-grasp Enabled**: True
- **Physics**: PyBullet with 240Hz timestep
- **Observation**: Dict space with multiple modalities

## Performance Targets

Based on the paper "High-Speed Autonomous Robotic Assembly Using In-Hand Manipulation and Re-Grasping":

| Metric | Paper Result | Our Target |
|--------|-------------|------------|
| Success Rate | 95% | 90%+ |
| Assembly Time | 60-115s | <120s |
| Re-grasp Rate | 25% | 20-30% |
| Pieces Placed | 7/7 | 7/7 |

## File Structure

```
├── soma_cube_gym_env.py      # Main environment implementation
├── ppo_soma_trainer.py       # PPO training script
├── re_grasp_module.py        # Re-grasping capability
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── models/                   # Saved models
├── logs/                     # Training logs
└── checkpoints/             # Training checkpoints
```

## Paper Implementation Details

### Multi-Stage Planning
The implementation follows the paper's multi-stage approach:
1. **Assembly Solver**: Determines piece placement sequence
2. **Sequence Planner**: Optimizes assembly order
3. **Grasp Planner**: Plans grasp configurations
4. **Motion Planner**: Executes assembly motions

### Vertical Pickup Constraint
- X-axis and Y-axis vertical grasps prioritized
- Z-axis vertical grasp for specific orientations
- Lateral grasps only when necessary

### Re-grasping Strategy
- **Grasp Failure Recovery**: Alternative grasp positions
- **Orientation Correction**: Piece rotation and re-grasp  
- **Collision Avoidance**: Alternative approach directions
- **In-hand Manipulation**: Piece adjustment while grasped

## Monitoring Training

### Tensorboard
```bash
tensorboard --logdir logs/
```

### Key Metrics
- **Success Rate**: Percentage of completed assemblies
- **Assembly Progress**: Average pieces placed per episode
- **Re-grasp Rate**: Percentage of actions requiring re-grasping
- **Episode Reward**: Cumulative reward per episode
- **Training Stability**: Loss curves and gradient norms

## Troubleshooting

### Common Issues

1. **PyBullet GUI Issues**
   ```bash
   # Use headless mode for training
   export DISPLAY=""  # Linux
   ```

2. **CUDA Memory Issues**
   ```bash
   # Reduce parallel environments
   python ppo_soma_trainer.py --n-envs 4
   ```

3. **Training Instability**
   ```bash
   # Lower learning rate
   python ppo_soma_trainer.py --learning-rate 1e-4
   ```

## Results Comparison

After training, the system should achieve:
- **Success Rate**: 85-95% (target: match paper's 95%)
- **Re-grasp Usage**: 20-30% of actions
- **Assembly Efficiency**: Complete assembly in <500 steps
- **Piece Placement**: Average 6+ pieces per episode during training

## Future Enhancements

1. **Domain Randomization**: Varying piece sizes, friction, lighting
2. **Real Robot Transfer**: Sim-to-real transfer optimization  
3. **Multi-robot Assembly**: Parallel assembly with multiple arms
4. **Vision Integration**: Real RGB-D camera input
5. **Advanced Re-grasping**: Learning-based re-grasp strategy selection

## References

1. *"High-Speed Autonomous Robotic Assembly Using In-Hand Manipulation and Re-Grasping"* - Primary implementation reference
2. Stable-Baselines3 Documentation
3. OpenAI Gymnasium Documentation
4. PyBullet Quickstart Guide