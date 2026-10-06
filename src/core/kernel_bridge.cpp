#include "rendition/kernel_bridge.hpp"
#include "rendition/generated_spectral_basis.hpp"
#include <algorithm>
namespace rendition {
namespace {
rendition_kernel::M3 convert(const Mat3 &m) {
    rendition_kernel::M3 k;
    for (int i = 0; i < 9; i++)
        k.a[i] = float(m.v[i]);
    return k;
}
std::pair<double, double> daylight(double t, int version) {
    double x = t <= 7000 ? (version==0 ? -.4e9 / (t * t * t) + .7e6 / (t * t) + .289e3 / t + .266
                                       : -4.6070e9 / (t * t * t) + 2.9678e6 / (t * t) + .09911e3 / t + .244063)
                         : -2.0064e9 / (t * t * t) + 1.9018e6 / (t * t) + .24748e3 / t + .23704;
    return {x, -3 * x * x + 2.87 * x - .275};
}
} // namespace
rendition_kernel::Parameters kernelParameters(const Snapshot &s) {
    rendition_kernel::Parameters k{};
    for (int i = 0; i < rendition_kernel::P_COUNT; i++) {
        auto it = s.parameterValues().find(rendition_kernel::parameterNames[i]);
        if (it != s.parameterValues().end())
            k.v[i] = float(it->second);
    }
    k.effect = int(s.effectId());
    k.look = int(s.selectedLook());
    k.identity = s.isIdentity();
    k.toXYZ = convert(s.colorSpace().toXYZ);
    k.fromXYZ = convert(s.colorSpace().fromXYZ);
    k.toD65 = convert(s.toReferenceWhite());
    k.fromD65 = convert(s.fromReferenceWhite());
    k.matrix = convert(s.effectiveMatrix());
    k.whiteBalance = convert(Mat3{});
    k.inverseRecord = convert(Mat3{});
    if (s.effectId() == Effect::Scene && (s.get("temperature") != 6504 || s.get("tint") != 0)) {
        int version=int(s.get("illuminantVersion"));
        auto xy = daylight(s.get("temperature"),version), base = daylight(6504,version);
        xy.first += (version==0?s.colorSpace().wx:.3127) - base.first;
        xy.second += (version==0?s.colorSpace().wy:.3290) - base.second;
        double den = -2 * xy.first + 12 * xy.second + 3, u = 4 * xy.first / den,
               v = 6 * xy.second / den + s.get("tint"), D = 2 * u - 8 * v + 4, x = 3 * u / D, y = 2 * v / D;
        if(version==0) {
            // Frozen historical Scene mapping, including its lower polynomial.
            k.whiteBalance=convert(s.colorSpace().fromXYZ *
                adaptation(x,y,s.colorSpace().wx,s.colorSpace().wy,int(s.get("adaptation"))) * s.colorSpace().toXYZ);
        } else {
            // Corrected daylight in common D65 coordinates; input gamut only
            // determines conversion, not a different illuminant trajectory.
            k.whiteBalance=convert(s.colorSpace().fromXYZ * s.fromReferenceWhite() *
                adaptation(x,y,.3127,.3290,int(s.get("adaptation"))) *
                s.toReferenceWhite() * s.colorSpace().toXYZ);
        }
    }
    if (s.effectId() == Effect::Strip && s.get("mode") == 2 && !s.isIdentity())
        k.inverseRecord = convert(s.effectiveMatrix().inverse());
    return k;
}
const std::vector<float> &spectralTable() {
    static const auto table = []() {
        std::vector<float> a;
        for (auto &models : spectral_basis::response)
            for (auto &family : models)
                for (auto &level : family)
                    for (double v : level)
                        a.push_back(float(v));
        return a;
    }();
    return table;
}
rendition_kernel::M3 spectralBasis(bool inverse) {
    rendition_kernel::M3 b;
    for (int i = 0; i < 9; i++)
        b.a[i] = float(inverse ? spectral_basis::inverseB[i] : spectral_basis::B[i]);
    return b;
}
Vec3 kernelApply(const Snapshot &s, Vec3 rgb) {
    if(s.effectId()>=Effect::Primaries) throw std::invalid_argument("Artist Primaries prototype requires CPU model dispatch");
    auto r = rendition_kernel::run(s.packed(), {rgb.x, rgb.y, rgb.z}, spectralTable().data(), spectralBasis(),
                                   spectralBasis(true));
    if (r.error == 1)
        throw std::domain_error("Nonfinite source RGB: use Inspector NaN / Inf mode");
    if (r.error == 2)
        throw std::domain_error("Selected domain requires positive inputs or finite input produced nonfinite "
                                "RGB; inspect domain/parameters");
    if (r.error == 3)
        throw std::invalid_argument("Inspector procedural mode requires image geometry / Reference clip");
    return {r.rgb.x, r.rgb.y, r.rgb.z};
}
} // namespace rendition
