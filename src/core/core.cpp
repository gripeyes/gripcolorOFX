#include "rendition/core.hpp"
#include "rendition/kernel_math.hpp"
#include <algorithm>
#include <limits>
namespace rendition {
Vec3 Mat3::operator*(Vec3 x) const {
    return {float(v[0] * x.x + v[1] * x.y + v[2] * x.z), float(v[3] * x.x + v[4] * x.y + v[5] * x.z),
            float(v[6] * x.x + v[7] * x.y + v[8] * x.z)};
}
Mat3 Mat3::operator*(const Mat3 &b) const {
    Mat3 o;
    o.v.fill(0);
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            for (int k = 0; k < 3; k++)
                o.v[i * 3 + j] += v[i * 3 + k] * b.v[k * 3 + j];
    return o;
}
Mat3 Mat3::inverse() const {
    const auto &a = v;
    double det = a[0] * (a[4] * a[8] - a[5] * a[7]) - a[1] * (a[3] * a[8] - a[5] * a[6]) +
                 a[2] * (a[3] * a[7] - a[4] * a[6]);
    if (!std::isfinite(det) || std::abs(det) < 1e-12)
        throw std::invalid_argument("Singular or invalid color matrix");
    Mat3 r;
    r.v = {a[4] * a[8] - a[5] * a[7], a[2] * a[7] - a[1] * a[8], a[1] * a[5] - a[2] * a[4],
           a[5] * a[6] - a[3] * a[8], a[0] * a[8] - a[2] * a[6], a[2] * a[3] - a[0] * a[5],
           a[3] * a[7] - a[4] * a[6], a[1] * a[6] - a[0] * a[7], a[0] * a[4] - a[1] * a[3]};
    for (auto &t : r.v)
        t /= det;
    return r;
}
Vec3 whiteXYZ(double x, double y) {
    if (!std::isfinite(x) || !std::isfinite(y) || y <= 0 || x <= 0 || x + y > 1.0000001)
        throw std::invalid_argument("Invalid xy chromaticity");
    return {float(x / y), 1, float((1 - x - y) / y)};
}
ColorSpace ColorSpace::make(Gamut gamut, Chromaticities c) {
    if (gamut == Gamut::Rec2020)
        c = {.708, .292, .170, .797, .131, .046, .3127, .3290};
    if (gamut == Gamut::AP1)
        c = {.713, .293, .165, .830, .128, .044, .32168, .33767};
    if (gamut == Gamut::Rec709)
        c = {.64, .33, .30, .60, .15, .06, .3127, .3290};
    // AP1's red primary intentionally has x+y > 1; imaginary primaries are allowed.
    const double x[3] = {c.rx, c.gx, c.bx}, y[3] = {c.ry, c.gy, c.by};
    Mat3 p;
    for (int j = 0; j < 3; j++) {
        if (!std::isfinite(x[j]) || !std::isfinite(y[j]) || y[j] <= 0 || x[j] < 0 || x[j] > 1 || y[j] > 1)
            throw std::invalid_argument("Invalid primary chromaticity");
        p.v[j] = x[j] / y[j];
        p.v[3 + j] = 1;
        p.v[6 + j] = (1 - x[j] - y[j]) / y[j];
    }
    // Solve in double precision: matrix constants do not inherit float white error.
    auto inv = p.inverse();
    double w[3] = {c.wx / c.wy, 1, (1 - c.wx - c.wy) / c.wy};
    whiteXYZ(c.wx, c.wy);
    double s[3]{};
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            s[i] += inv.v[i * 3 + j] * w[j];
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            p.v[i * 3 + j] *= s[j];
    return {p, p.inverse(), c.wx, c.wy};
}
ColorSpace interpret(int m, const std::string &tag, Chromaticities c) {
    if (m >= 1 && m <= 4)
        return ColorSpace::make(static_cast<Gamut>(m - 1), c);
    if (m != 0)
        throw std::invalid_argument("Invalid interpretation selection");
    // Deliberately exact allowlist, never a substring guess at arbitrary OCIO names.
    if (tag == "ACEScg" || tag == "ACES - ACEScg")
        return ColorSpace::make(Gamut::AP1);
    if (tag == "lin_rec2020" || tag == "Linear Rec.2020" || tag == "Linear Rec.2020 (D65)")
        return ColorSpace::make(Gamut::Rec2020);
    if (tag == "lin_rec709_srgb" || tag == "Linear Rec.709" || tag == "Linear Rec.709 (sRGB)")
        return ColorSpace::make(Gamut::Rec709);
    throw std::invalid_argument(
        "Unspecified / Interpretation Required: select source primaries and white point manually");
}
Mat3 adaptation(double sx, double sy, double dx, double dy, int method) {
    Mat3 cone;
    if (method == 0)
        cone.v = {.8951, .2664, -.1614, -.7502, 1.7135, .0367, .0389, -.0685, 1.0296};
    else if (method == 1)
        cone.v = {.401288, .650173, -.051461, -.250268, 1.204414, .045854, -.002079, .048952, .953127};
    else if (method == 2)
        cone.v = {1, 0, 0, 0, 1, 0, 0, 0, 1};
    else
        throw std::invalid_argument("Unknown adaptation method");
    auto a = cone * whiteXYZ(sx, sy), b = cone * whiteXYZ(dx, dy);
    Mat3 d;
    d.v = {b.x / a.x, 0, 0, 0, b.y / a.y, 0, 0, 0, b.z / a.z};
    return cone.inverse() * d * cone;
}
float encode(float x, LookDomain d) {
    int n = int(d);
    if (n < 0 || n > 5)
        throw std::invalid_argument("Unknown look domain");
    if ((n == 0 || n == 4) && x <= 0)
        throw std::domain_error("Pure stop space requires positive input");
    return rendition_kernel::encode(x, n);
}
float decode(float x, LookDomain d) {
    int n = int(d);
    if (n < 0 || n > 5)
        throw std::invalid_argument("Unknown look domain");
    return rendition_kernel::decode(x, n);
}
float grayCode(LookDomain d) {
    return encode(.18f, d);
}
float stopSlope(LookDomain d) {
    return rendition_kernel::slope(int(d));
}
Vec3 encode(Vec3 x, LookDomain d) {
    return {encode(x.x, d), encode(x.y, d), encode(x.z, d)};
}
Vec3 decode(Vec3 x, LookDomain d) {
    return {decode(x.x, d), decode(x.y, d), decode(x.z, d)};
}
float wrap(float x) {
    return x - 360.f * std::floor(x / 360.f);
}
float smooth(float a, float b, float x) {
    if (!(b > a))
        return x >= b ? 1 : 0;
    float t = std::clamp((x - a) / (b - a), 0.f, 1.f);
    return t * t * (3 - 2 * t);
}
float signedPower(float x, float p) {
    return std::copysign(std::pow(std::abs(x), p), x);
}
float exposure(Vec3 rgb, const ColorSpace &s) {
    float y = (s.toXYZ * rgb).y;
    return y > 0 ? std::log2(y / .18f) : -std::numeric_limits<float>::infinity();
}
} // namespace rendition
