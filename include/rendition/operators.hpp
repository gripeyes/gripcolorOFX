#pragma once
#include "core.hpp"
#include <map>
#include <memory>
namespace rendition_kernel {
struct Parameters;
}
namespace rendition {
enum class Effect { Scene, Tone, Volume, Density, Crossover, Crosstalk, Strip, Inspector, Primaries, Base, Palette, Material };
using Values = std::map<std::string, double>;
struct Parameter {
    std::string id, label, group, unit;
    double value, lo, hi;
    std::vector<std::string> choices;
};
const char *name(Effect effect);
std::vector<Parameter> parameters(Effect effect);
struct Semantic {
    std::string domain, reference, exposure, invertibility, gamut, negative, hdr, neutralAxis,
        neutralMagnitude, gamutDependence, status, limitations;
};
Semantic semantics(Effect effect, const Values &values = {});
Vec3 oklab(Vec3 xyz);
Vec3 oklabInverse(Vec3 lab);
class PrimariesModel;
class Snapshot {
    Effect effect;
    ColorSpace space;
    Values values;
    LookDomain look;
    Mat3 toD65, fromD65, matrix;
    bool identity;
    std::shared_ptr<const Snapshot> diagnosticProbe;
    std::shared_ptr<const PrimariesModel> primaries;
    std::shared_ptr<const Snapshot> illuminantStage;
    std::vector<std::shared_ptr<const Snapshot>> stages;
    std::shared_ptr<const rendition_kernel::Parameters> kernel;

  public:
    Effect effectId() const {
        return effect;
    }
    const ColorSpace &colorSpace() const {
        return space;
    }
    const Values &parameterValues() const {
        return values;
    }
    LookDomain selectedLook() const {
        return look;
    }
    const Mat3 &toReferenceWhite() const {
        return toD65;
    }
    const Mat3 &fromReferenceWhite() const {
        return fromD65;
    }
    const Mat3 &effectiveMatrix() const {
        return matrix;
    }
    bool isIdentity() const {
        return identity;
    }
    const rendition_kernel::Parameters &packed() const {
        return *kernel;
    }
    float get(const std::string &key) const;
    Snapshot(Effect effect, const Values &values = {}, const std::string &metadata = "");
    Vec3 apply(Vec3 rgb) const;
    std::array<float, 4> pixel(std::array<float, 4> rgba, float matteCoverage = 1) const;
};
struct ImageView {
    float *data;
    int x1, y1, x2, y2;
    ptrdiff_t rowBytes;
    int components;
    float *at(int x, int y) const;
};
void renderWindow(const Snapshot &snapshot, const ImageView &src, const ImageView &dst, int x1, int y1,
                  int x2, int y2);
} // namespace rendition
