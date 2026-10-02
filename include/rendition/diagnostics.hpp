#pragma once
#include "operators.hpp"
namespace rendition {
struct Differential {
    Mat3 jacobian;
    double determinant;
    std::array<double, 3> singularValues; // descending
    double condition;
    double stepDisagreement; // relative Frobenius difference between h and h/2
    bool reliable;
};
// RGB-to-RGB differential of the configured operator, not a perceptual metric.
Differential differential(const Snapshot &operation, Vec3 rgb, double relativeStep = .002);
Vec3 differentialView(const Differential &result, int mode);
}
