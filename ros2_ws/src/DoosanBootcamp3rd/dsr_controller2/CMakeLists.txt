cmake_minimum_required(VERSION 3.16)
project(dsr_controller2 LANGUAGES CXX)

if(CMAKE_CXX_COMPILER_ID MATCHES "(GNU|Clang)")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Required dependencies
set(THIS_PACKAGE_INCLUDE_DEPENDS
  pluginlib
  rclcpp
  rclcpp_lifecycle
  dsr_msgs2
  trajectory_msgs
  std_msgs
  rclcpp_components
  ament_index_cpp
  yaml-cpp
)

# Optional control dependencies
set(OPTIONAL_DEPENDS
  forward_command_controller
  controller_interface
  hardware_interface
  moveit_msgs
  control_msgs
  dsr_hardware2
)

find_package(ament_cmake REQUIRED)
find_package(backward_ros QUIET)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()
foreach(Dependency IN ITEMS ${OPTIONAL_DEPENDS})
  find_package(${Dependency} QUIET)
endforeach()

if(NOT DEFINED DRCF_VER)
        set(DRCF_VER 2)
endif()
message(DRCF_VERSION : ${DRCF_VER})


SET( COMMON_INC_FILES
  ../dsr_common2/include
)
SET( COMMON_LIB_FILES
  ../dsr_common2/lib
)

include_directories(
  include
  ${Boost_INCLUDE_DIRS}
  ${COMMON_INC_FILES}
)

LINK_LIBRARIES(DRFL PocoFoundation PocoNet)

if($ENV{ROS_DISTRO} STREQUAL "humble")                          
  LINK_DIRECTORIES ("${COMMON_LIB_FILES}/$ENV{ROS_DISTRO}/x86_64")
else()
  message("Unknown ROS distro:")
  message($ENV{ROS_DISTRO})
endif()
# add_executable(dsr_control_node2 src/dsr_control_node2.cpp)
# ament_target_dependencies(
#   dsr_control_node2 PUBLIC
#   ${THIS_PACKAGE_INCLUDE_DEPENDS}
# )

# Only build if controller_interface is available
if(controller_interface_FOUND)
  add_library(dsr_controller2 SHARED
    # src/dsr_control_node2.cpp
    src/dsr_controller2.cpp
    # src/dsr_joint_trajectory.cpp
  )
target_compile_definitions(${PROJECT_NAME} PUBLIC DRCF_VERSION=${DRCF_VER})
target_compile_features(dsr_controller2 PUBLIC cxx_std_17)
target_include_directories(dsr_controller2 PUBLIC
  $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/dsr_controller2>
)
ament_target_dependencies(dsr_controller2 PUBLIC ${THIS_PACKAGE_INCLUDE_DEPENDS})

endif()

# Only build if control_msgs is available
if(control_msgs_FOUND)
  add_library(dsr_joint_trajectory SHARED
    # src/joint_group_velocity_controller.cpp
    src/dsr_joint_trajectory.cpp
  )
target_compile_features(dsr_joint_trajectory PUBLIC cxx_std_17)
target_include_directories(dsr_joint_trajectory PUBLIC
  $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/dsr_joint_trajectory>
  )
  ament_target_dependencies(dsr_joint_trajectory PUBLIC ${THIS_PACKAGE_INCLUDE_DEPENDS})
  
  # Causes the visibility macros to use dllexport rather than dllimport,
  # which is appropriate when building the dll but not consuming it.
  target_compile_definitions(dsr_joint_trajectory PRIVATE "DSR_CONTROLLER2_BUILDING_DLL")
endif()

# Only set this if the controller was built
if(controller_interface_FOUND)
  target_compile_definitions(dsr_controller2 PRIVATE "DSR_CONTROLLER2_BUILDING_DLL")
endif()


# Only export plugins if controller_interface is available
if(controller_interface_FOUND)
  pluginlib_export_plugin_description_file(controller_interface dsr_controller2_plugins.xml)
endif()
if(control_msgs_FOUND)
  pluginlib_export_plugin_description_file(controller_interface dsr_joint_trajectory_plugin.xml)
endif()


install(
  DIRECTORY include/
  DESTINATION include/dsr_controller2
)
install(
  DIRECTORY config launch
  DESTINATION share/dsr_controller2
)
# install(
#   TARGETS dsr_control_node2
#   # RUNTIME DESTINATION bin
#   ARCHIVE DESTINATION lib
#   LIBRARY DESTINATION lib
#   RUNTIME DESTINATION lib/${PROJECT_NAME}
# )

if(controller_interface_FOUND)
  install(
    TARGETS
    dsr_controller2
    EXPORT export_dsr_controller2
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
  )
endif()
if(control_msgs_FOUND)
  install(
    TARGETS
    dsr_joint_trajectory
    EXPORT export_dsr_joint_trajectory
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
  )
endif()

if(controller_interface_FOUND)
  ament_export_targets(export_dsr_controller2 HAS_LIBRARY_TARGET)
endif()
if(control_msgs_FOUND)
  ament_export_targets(export_dsr_joint_trajectory HAS_LIBRARY_TARGET)
endif()
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()
