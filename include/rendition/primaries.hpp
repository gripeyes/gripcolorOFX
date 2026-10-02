#pragma once
#include "operators.hpp"
namespace rendition {
// CPU artist prototype; all processing remains pointwise and scene compatible.
class PrimariesModel {
    Values v;
    Mat3 toReference, fromReference, artistToXYZ;
    Vec3 white, warmAxis, greenAxis, shadowAxis, highlightAxis;
    double get(const char *key) const;
  public:
    explicit PrimariesModel(const Snapshot &snapshot);
    Vec3 apply(Vec3 rgb) const;
};
std::vector<Parameter> primariesParameters();
}
