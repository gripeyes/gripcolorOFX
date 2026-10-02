#pragma once
#include "kernel_math.hpp"
#include "operators.hpp"
namespace rendition {
rendition_kernel::Parameters kernelParameters(const Snapshot &s);
const std::vector<float> &spectralTable();
rendition_kernel::M3 spectralBasis(bool inverse = false);
Vec3 kernelApply(const Snapshot &s, Vec3 rgb);
} // namespace rendition
