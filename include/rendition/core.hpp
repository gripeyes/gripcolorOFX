#pragma once
#include <array>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>
namespace rendition {
struct Vec3 {
    float x{}, y{}, z{};
    float &operator[](size_t i) {
        return i == 0 ? x : i == 1 ? y : z;
    }
    float operator[](size_t i) const {
        return i == 0 ? x : i == 1 ? y : z;
    }
};
inline Vec3 operator+(Vec3 a, Vec3 b) {
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}
inline Vec3 operator-(Vec3 a, Vec3 b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}
inline Vec3 operator*(Vec3 a, float s) {
    return {a.x * s, a.y * s, a.z * s};
}
inline bool finite(Vec3 a) {
    return std::isfinite(a.x) && std::isfinite(a.y) && std::isfinite(a.z);
}
struct Mat3 {
    std::array<double, 9> v{1, 0, 0, 0, 1, 0, 0, 0, 1};
    Vec3 operator*(Vec3 x) const;
    Mat3 operator*(const Mat3 &b) const;
    Mat3 inverse() const;
};
struct Chromaticities {
    double rx, ry, gx, gy, bx, by, wx, wy;
};
enum class Gamut { Rec2020, AP1, Rec709, Custom };
struct ColorSpace {
    Mat3 toXYZ, fromXYZ;
    double wx, wy;
    static ColorSpace make(Gamut gamut,
                           Chromaticities custom = {.708, .292, .170, .797, .131, .046, .3127, .3290});
};
// None is not a gamut; unresolved Auto never resolves to a preset.
ColorSpace interpret(int manual, const std::string &metadata,
                     Chromaticities custom = {.708, .292, .170, .797, .131, .046, .3127, .3290});
Vec3 whiteXYZ(double x, double y);
Mat3 adaptation(double sx, double sy, double dx, double dy, int method = 0);
enum class LookDomain { Stops, ACEScct, LogC4, DaVinci, AgXStops, LookLog };
float encode(float x, LookDomain d);
float decode(float x, LookDomain d);
float grayCode(LookDomain d);
float stopSlope(LookDomain d);
Vec3 encode(Vec3 x, LookDomain d);
Vec3 decode(Vec3 x, LookDomain d);
float wrap(float degrees);
float smooth(float a, float b, float x);
float signedPower(float x, float p);
float exposure(Vec3 rgb, const ColorSpace &space); // positive Y only; nonpositive has no physical EV
} // namespace rendition
