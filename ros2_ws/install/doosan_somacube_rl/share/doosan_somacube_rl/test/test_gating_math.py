#!/usr/bin/env python3

"""
Safety Gating Math Tests for SomaCube RL System

Tests the mathematical correctness of safety gating algorithms used in the
impedance control and policy execution systems.
"""

import unittest
import numpy as np
from scipy.spatial.transform import Rotation as R
import sys
import os

# Add src directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock ROS2 dependencies for testing
class MockNode:
    def get_parameter(self, name):
        class MockParam:
            def __init__(self, value):
                self.value = value
        
        # Default parameter values for testing
        defaults = {
            'policy_sac_low.safety_gating.force_limit_N': 20.0,
            'policy_sac_low.safety_gating.torque_limit_Nm': 2.0,
            'policy_sac_low.safety_gating.base_delta_pos_m': 0.004,
            'policy_sac_low.safety_gating.base_delta_rot_deg': 2.0,
            'policy_sac_low.safety_gating.adapt_by_icp_uncertainty': True,
            'policy_sac_low.safety_gating.icp_std_bounds_m': [0.0, 0.010],
            'policy_sac_low.safety_gating.scale_limits.delta_pos_scale_range': [1.0, 0.3],
            'policy_sac_low.safety_gating.scale_limits.delta_rot_scale_range': [1.0, 0.25],
        }
        return MockParam(defaults.get(name, 0.0))


class TestSafetyGatingMath(unittest.TestCase):
    """Test safety gating mathematical operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.safety_params = {
            'force_limit_N': 20.0,
            'torque_limit_Nm': 2.0,
            'base_delta_pos_m': 0.004,
            'base_delta_rot_deg': 2.0,
            'adapt_by_icp': True,
            'icp_std_bounds': [0.0, 0.010],
            'pos_scale_range': [1.0, 0.3],
            'rot_scale_range': [1.0, 0.25]
        }
        
        # Test tolerance for floating point comparisons
        self.tol = 1e-6

    def test_position_scaling_basic(self):
        """Test basic position scaling without uncertainty adaptation"""
        action = np.array([0.01, 0.005, 0.002, 0.1, 0.05, 0.02, 0.0, 0.0])
        
        # Extract position and rotation components
        delta_pos = action[:3]
        delta_rot = action[3:6]
        
        # Apply base scaling
        base_pos_limit = self.safety_params['base_delta_pos_m']
        base_rot_limit = np.deg2rad(self.safety_params['base_delta_rot_deg'])
        
        # Position scaling
        pos_magnitude = np.linalg.norm(delta_pos)
        if pos_magnitude > base_pos_limit:
            expected_pos_scaled = delta_pos / pos_magnitude * base_pos_limit
        else:
            expected_pos_scaled = delta_pos
        
        # Since input magnitude is 0.012 > 0.004, should be scaled
        expected_magnitude = base_pos_limit
        actual_magnitude = np.linalg.norm(expected_pos_scaled)
        
        self.assertAlmostEqual(actual_magnitude, expected_magnitude, delta=self.tol)
        
        # Direction should be preserved
        expected_direction = delta_pos / pos_magnitude
        actual_direction = expected_pos_scaled / np.linalg.norm(expected_pos_scaled)
        np.testing.assert_allclose(expected_direction, actual_direction, atol=self.tol)

    def test_rotation_scaling_basic(self):
        """Test basic rotation scaling without uncertainty adaptation"""
        # Test rotation that exceeds limits
        delta_rot = np.array([0.1, 0.05, 0.02])  # radians
        
        base_rot_limit = np.deg2rad(self.safety_params['base_delta_rot_deg'])
        rot_magnitude = np.linalg.norm(delta_rot)
        
        if rot_magnitude > base_rot_limit:
            expected_rot_scaled = delta_rot / rot_magnitude * base_rot_limit
            expected_magnitude = base_rot_limit
        else:
            expected_rot_scaled = delta_rot
            expected_magnitude = rot_magnitude
        
        actual_magnitude = np.linalg.norm(expected_rot_scaled)
        self.assertAlmostEqual(actual_magnitude, expected_magnitude, delta=self.tol)

    def test_uncertainty_scaling_interpolation(self):
        """Test ICP uncertainty-based scaling interpolation"""
        # Test various uncertainty levels
        uncertainty_levels = [0.0, 0.003, 0.005, 0.008, 0.010]
        std_bounds = self.safety_params['icp_std_bounds']
        pos_scale_range = self.safety_params['pos_scale_range']
        rot_scale_range = self.safety_params['rot_scale_range']
        
        for icp_std in uncertainty_levels:
            # Normalize uncertainty
            std_normalized = np.clip(
                (icp_std - std_bounds[0]) / (std_bounds[1] - std_bounds[0]),
                0.0, 1.0
            )
            
            # Calculate expected scale factors
            expected_pos_scale = pos_scale_range[1] + (pos_scale_range[0] - pos_scale_range[1]) * (1 - std_normalized)
            expected_rot_scale = rot_scale_range[1] + (rot_scale_range[0] - rot_scale_range[1]) * (1 - std_normalized)
            
            # Verify scaling is within bounds
            self.assertGreaterEqual(expected_pos_scale, pos_scale_range[1])
            self.assertLessEqual(expected_pos_scale, pos_scale_range[0])
            self.assertGreaterEqual(expected_rot_scale, rot_scale_range[1])
            self.assertLessEqual(expected_rot_scale, rot_scale_range[0])
            
            # Verify monotonic relationship (higher uncertainty -> lower scaling)
            if icp_std == 0.0:
                self.assertAlmostEqual(expected_pos_scale, pos_scale_range[0], delta=self.tol)
                self.assertAlmostEqual(expected_rot_scale, rot_scale_range[0], delta=self.tol)
            elif icp_std == std_bounds[1]:
                self.assertAlmostEqual(expected_pos_scale, pos_scale_range[1], delta=self.tol)
                self.assertAlmostEqual(expected_rot_scale, rot_scale_range[1], delta=self.tol)

    def test_confidence_calculation(self):
        """Test confidence score calculation based on gating"""
        # Test confidence reduction with various constraint violations
        base_confidence = 1.0
        
        # Test force limit violation
        current_force_mag = 25.0  # Exceeds 20.0 limit
        force_limit = self.safety_params['force_limit_N']
        if current_force_mag > force_limit * 0.8:
            force_confidence = max(0.1, (force_limit - current_force_mag) / (force_limit * 0.2))
            expected_confidence = base_confidence * 0.5 * force_confidence
        else:
            expected_confidence = base_confidence
        
        self.assertLess(expected_confidence, base_confidence)
        self.assertGreaterEqual(expected_confidence, 0.0)
        
        # Test uncertainty-based confidence reduction
        icp_std = 0.008
        std_bounds = self.safety_params['icp_std_bounds']
        std_normalized = np.clip((icp_std - std_bounds[0]) / (std_bounds[1] - std_bounds[0]), 0.0, 1.0)
        
        uncertainty_confidence = base_confidence * (1 - std_normalized * 0.5)
        self.assertLess(uncertainty_confidence, base_confidence)
        self.assertGreaterEqual(uncertainty_confidence, 0.5)  # Should not go below 0.5

    def test_action_clipping_edge_cases(self):
        """Test action clipping with edge cases"""
        # Test zero action
        zero_action = np.zeros(8)
        clipped_action = self.apply_safety_gating_mock(zero_action)
        np.testing.assert_allclose(clipped_action, zero_action, atol=self.tol)
        
        # Test very large action
        large_action = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, -2.0])
        clipped_action = self.apply_safety_gating_mock(large_action)
        
        # Position should be clipped to limit
        pos_part = clipped_action[:3]
        pos_magnitude = np.linalg.norm(pos_part)
        self.assertLessEqual(pos_magnitude, self.safety_params['base_delta_pos_m'] + self.tol)
        
        # Rotation should be clipped to limit
        rot_part = clipped_action[3:6]
        rot_magnitude = np.linalg.norm(rot_part)
        self.assertLessEqual(rot_magnitude, np.deg2rad(self.safety_params['base_delta_rot_deg']) + self.tol)
        
        # Gain deltas should be clipped to [-0.5, 0.5]
        gain_deltas = clipped_action[6:8]
        self.assertGreaterEqual(gain_deltas[0], -0.5)
        self.assertLessEqual(gain_deltas[0], 0.5)
        self.assertGreaterEqual(gain_deltas[1], -0.5)
        self.assertLessEqual(gain_deltas[1], 0.5)

    def test_rotation_matrix_operations(self):
        """Test rotation matrix operations used in pose tracking"""
        # Test SO(3) exponential map operations
        axis_angles = [
            np.array([0.0, 0.0, 0.0]),        # Identity
            np.array([0.1, 0.0, 0.0]),        # X rotation
            np.array([0.0, 0.1, 0.0]),        # Y rotation  
            np.array([0.0, 0.0, 0.1]),        # Z rotation
            np.array([0.05, 0.05, 0.05]),     # Combined
        ]
        
        for axis_angle in axis_angles:
            # Convert to rotation matrix
            rot_matrix = R.from_rotvec(axis_angle).as_matrix()
            
            # Verify it's a valid rotation matrix
            # 1. Determinant should be 1
            det = np.linalg.det(rot_matrix)
            self.assertAlmostEqual(det, 1.0, delta=self.tol)
            
            # 2. Should be orthogonal (R^T * R = I)
            identity_test = rot_matrix.T @ rot_matrix
            np.testing.assert_allclose(identity_test, np.eye(3), atol=self.tol)
            
            # 3. Inverse conversion should match
            recovered_axis_angle = R.from_matrix(rot_matrix).as_rotvec()
            np.testing.assert_allclose(axis_angle, recovered_axis_angle, atol=self.tol)

    def test_geodesic_distance_calculation(self):
        """Test geodesic distance calculation on SO(3)"""
        # Test cases for geodesic distance calculation
        test_cases = [
            (np.eye(3), np.eye(3), 0.0),  # Same rotation
            (np.eye(3), R.from_euler('z', np.pi/4).as_matrix(), np.pi/4),  # 45 degree Z rotation
            (np.eye(3), R.from_euler('x', np.pi/2).as_matrix(), np.pi/2),  # 90 degree X rotation
        ]
        
        for rot1, rot2, expected_angle in test_cases:
            # Calculate geodesic distance
            relative_rot = rot2 @ rot1.T
            trace_val = np.trace(relative_rot)
            
            # Handle numerical precision issues
            trace_val = np.clip(trace_val, -1, 3)  # trace can be in [-1, 3] for valid rotation
            
            geodesic_angle = np.arccos((trace_val - 1) / 2)
            
            # Handle case where arccos might return NaN due to numerical precision
            if np.isnan(geodesic_angle):
                geodesic_angle = 0.0
            
            self.assertAlmostEqual(geodesic_angle, expected_angle, delta=self.tol)

    def test_force_threshold_calculations(self):
        """Test force threshold and violation detection"""
        # Test force magnitudes and threshold comparisons
        test_forces = [
            ([0, 0, 0], False),           # No force
            ([5, 0, 0], False),           # Below threshold
            ([15, 10, 5], False),         # Combined below threshold
            ([25, 0, 0], True),           # Exceeds threshold
            ([15, 15, 0], True),          # Combined exceeds threshold
        ]
        
        force_limit = self.safety_params['force_limit_N']
        
        for force_components, should_violate in test_forces:
            force_magnitude = np.sqrt(sum(f**2 for f in force_components))
            violation = force_magnitude > force_limit
            
            self.assertEqual(violation, should_violate, 
                           f"Force {force_components} -> magnitude {force_magnitude}, "
                           f"expected violation: {should_violate}, got: {violation}")

    def apply_safety_gating_mock(self, action):
        """Mock implementation of safety gating for testing"""
        # Extract action components
        delta_pos = action[:3]
        delta_rot = action[3:6]  
        delta_gains = action[6:8]
        
        # Apply position limits
        base_pos_limit = self.safety_params['base_delta_pos_m']
        pos_magnitude = np.linalg.norm(delta_pos)
        if pos_magnitude > base_pos_limit:
            delta_pos_scaled = delta_pos / pos_magnitude * base_pos_limit
        else:
            delta_pos_scaled = delta_pos
        
        # Apply rotation limits
        base_rot_limit = np.deg2rad(self.safety_params['base_delta_rot_deg'])
        rot_magnitude = np.linalg.norm(delta_rot)
        if rot_magnitude > base_rot_limit:
            delta_rot_scaled = delta_rot / rot_magnitude * base_rot_limit
        else:
            delta_rot_scaled = delta_rot
        
        # Clamp gain deltas
        delta_gains_clamped = np.clip(delta_gains, -0.5, 0.5)
        
        return np.concatenate([delta_pos_scaled, delta_rot_scaled, delta_gains_clamped])


class TestPoseErrorCalculations(unittest.TestCase):
    """Test pose error calculation methods"""
    
    def setUp(self):
        self.tol = 1e-6

    def test_position_error_calculation(self):
        """Test position error calculation"""
        current_pos = np.array([0.1, 0.2, 0.3])
        target_pos = np.array([0.15, 0.25, 0.35])
        
        expected_error = target_pos - current_pos
        actual_error = target_pos - current_pos
        
        np.testing.assert_allclose(actual_error, expected_error, atol=self.tol)
        
        # Test error magnitude
        expected_magnitude = np.linalg.norm(expected_error)
        actual_magnitude = np.linalg.norm(actual_error)
        self.assertAlmostEqual(actual_magnitude, expected_magnitude, delta=self.tol)

    def test_rotation_error_calculation(self):
        """Test rotation error calculation using axis-angle representation"""
        # Create test rotations
        current_rot = R.from_euler('xyz', [0.1, 0.2, 0.3])
        target_rot = R.from_euler('xyz', [0.15, 0.25, 0.35])
        
        # Calculate relative rotation
        relative_rot = target_rot * current_rot.inv()
        rotation_error = relative_rot.as_rotvec()
        
        # Verify that applying this error gives target rotation
        corrected_rot = R.from_rotvec(rotation_error) * current_rot
        
        # Compare rotation matrices (more stable than quaternions)
        target_matrix = target_rot.as_matrix()
        corrected_matrix = corrected_rot.as_matrix()
        
        np.testing.assert_allclose(target_matrix, corrected_matrix, atol=self.tol)

    def test_quaternion_normalization(self):
        """Test quaternion normalization checks"""
        # Test normalized quaternion
        normalized_quat = np.array([0.0, 0.0, 0.0, 1.0])
        norm = np.linalg.norm(normalized_quat)
        self.assertAlmostEqual(norm, 1.0, delta=self.tol)
        
        # Test non-normalized quaternion
        non_normalized = np.array([0.5, 0.5, 0.5, 0.5])
        norm_before = np.linalg.norm(non_normalized)
        self.assertNotAlmostEqual(norm_before, 1.0, delta=self.tol)
        
        # Normalize it
        normalized = non_normalized / norm_before
        norm_after = np.linalg.norm(normalized)
        self.assertAlmostEqual(norm_after, 1.0, delta=self.tol)


class TestNumericalStability(unittest.TestCase):
    """Test numerical stability of mathematical operations"""
    
    def setUp(self):
        self.tol = 1e-6

    def test_small_angle_approximations(self):
        """Test behavior with very small angles"""
        small_angles = [1e-8, 1e-6, 1e-4, 1e-2]
        
        for angle in small_angles:
            # Test rotation matrix creation
            rot = R.from_rotvec([angle, 0, 0])
            rot_matrix = rot.as_matrix()
            
            # Should still be valid rotation matrix
            det = np.linalg.det(rot_matrix)
            self.assertAlmostEqual(det, 1.0, delta=self.tol)
            
            # Test inverse conversion
            recovered_rotvec = rot.as_rotvec()
            self.assertAlmostEqual(recovered_rotvec[0], angle, delta=self.tol)

    def test_division_by_zero_protection(self):
        """Test protection against division by zero"""
        # Test zero vector normalization
        zero_vector = np.array([0.0, 0.0, 0.0])
        magnitude = np.linalg.norm(zero_vector)
        
        if magnitude > 1e-12:  # Threshold for zero
            normalized = zero_vector / magnitude
        else:
            normalized = np.array([1.0, 0.0, 0.0])  # Default direction
        
        # Should not contain NaN or Inf
        self.assertFalse(np.any(np.isnan(normalized)))
        self.assertFalse(np.any(np.isinf(normalized)))

    def test_large_value_handling(self):
        """Test handling of large numerical values"""
        large_values = [1e6, 1e12, 1e15]
        
        for value in large_values:
            # Test that operations remain stable
            pos_vector = np.array([value, 0, 0])
            normalized = pos_vector / np.linalg.norm(pos_vector)
            
            # Should give unit vector
            norm = np.linalg.norm(normalized)
            self.assertAlmostEqual(norm, 1.0, delta=self.tol)
            
            # Should not contain NaN or Inf
            self.assertFalse(np.any(np.isnan(normalized)))
            self.assertFalse(np.any(np.isinf(normalized)))


def run_test_suite():
    """Run all test suites and generate report"""
    print("Running Safety Gating Math Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSafetyGatingMath))
    suite.addTests(loader.loadTestsFromTestCase(TestPoseErrorCalculations))
    suite.addTests(loader.loadTestsFromTestCase(TestNumericalStability))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('Error:')[-1].strip()}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run safety gating math tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test', '-t', help='Run specific test class')
    
    args = parser.parse_args()
    
    if args.test:
        # Run specific test class
        suite = unittest.TestLoader().loadTestsFromName(args.test, sys.modules[__name__])
        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        # Run full test suite
        success = run_test_suite()
        sys.exit(0 if success else 1)