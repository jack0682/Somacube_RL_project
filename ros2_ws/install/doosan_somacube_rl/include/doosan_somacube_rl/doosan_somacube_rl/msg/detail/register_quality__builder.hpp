// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__BUILDER_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "doosan_somacube_rl/msg/detail/register_quality__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace doosan_somacube_rl
{

namespace msg
{

namespace builder
{

class Init_RegisterQuality_stamp
{
public:
  explicit Init_RegisterQuality_stamp(::doosan_somacube_rl::msg::RegisterQuality & msg)
  : msg_(msg)
  {}
  ::doosan_somacube_rl::msg::RegisterQuality stamp(::doosan_somacube_rl::msg::RegisterQuality::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::doosan_somacube_rl::msg::RegisterQuality msg_;
};

class Init_RegisterQuality_geodesic_deg
{
public:
  explicit Init_RegisterQuality_geodesic_deg(::doosan_somacube_rl::msg::RegisterQuality & msg)
  : msg_(msg)
  {}
  Init_RegisterQuality_stamp geodesic_deg(::doosan_somacube_rl::msg::RegisterQuality::_geodesic_deg_type arg)
  {
    msg_.geodesic_deg = std::move(arg);
    return Init_RegisterQuality_stamp(msg_);
  }

private:
  ::doosan_somacube_rl::msg::RegisterQuality msg_;
};

class Init_RegisterQuality_icp_residual_std
{
public:
  explicit Init_RegisterQuality_icp_residual_std(::doosan_somacube_rl::msg::RegisterQuality & msg)
  : msg_(msg)
  {}
  Init_RegisterQuality_geodesic_deg icp_residual_std(::doosan_somacube_rl::msg::RegisterQuality::_icp_residual_std_type arg)
  {
    msg_.icp_residual_std = std::move(arg);
    return Init_RegisterQuality_geodesic_deg(msg_);
  }

private:
  ::doosan_somacube_rl::msg::RegisterQuality msg_;
};

class Init_RegisterQuality_inlier_ratio
{
public:
  explicit Init_RegisterQuality_inlier_ratio(::doosan_somacube_rl::msg::RegisterQuality & msg)
  : msg_(msg)
  {}
  Init_RegisterQuality_icp_residual_std inlier_ratio(::doosan_somacube_rl::msg::RegisterQuality::_inlier_ratio_type arg)
  {
    msg_.inlier_ratio = std::move(arg);
    return Init_RegisterQuality_icp_residual_std(msg_);
  }

private:
  ::doosan_somacube_rl::msg::RegisterQuality msg_;
};

class Init_RegisterQuality_chamfer_bidir_m
{
public:
  explicit Init_RegisterQuality_chamfer_bidir_m(::doosan_somacube_rl::msg::RegisterQuality & msg)
  : msg_(msg)
  {}
  Init_RegisterQuality_inlier_ratio chamfer_bidir_m(::doosan_somacube_rl::msg::RegisterQuality::_chamfer_bidir_m_type arg)
  {
    msg_.chamfer_bidir_m = std::move(arg);
    return Init_RegisterQuality_inlier_ratio(msg_);
  }

private:
  ::doosan_somacube_rl::msg::RegisterQuality msg_;
};

class Init_RegisterQuality_mean_point2plane_m
{
public:
  Init_RegisterQuality_mean_point2plane_m()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_RegisterQuality_chamfer_bidir_m mean_point2plane_m(::doosan_somacube_rl::msg::RegisterQuality::_mean_point2plane_m_type arg)
  {
    msg_.mean_point2plane_m = std::move(arg);
    return Init_RegisterQuality_chamfer_bidir_m(msg_);
  }

private:
  ::doosan_somacube_rl::msg::RegisterQuality msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::doosan_somacube_rl::msg::RegisterQuality>()
{
  return doosan_somacube_rl::msg::builder::Init_RegisterQuality_mean_point2plane_m();
}

}  // namespace doosan_somacube_rl

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__BUILDER_HPP_
