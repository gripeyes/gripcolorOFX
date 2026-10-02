#include "rendition/operators.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>
using namespace rendition;
int main() {
    float src[3 * 5 * 4], dst[3 * 5 * 4];
    for (int i = 0; i < 60; i++)
        src[i] = i % 4 == 3 ? .3f : float(i - 10);
    src[0] = std::numeric_limits<float>::quiet_NaN();
    Snapshot identity(Effect::Scene, {{"interpretation", 1}});
    ImageView a{src, 7, 11, 12, 14, 80, 4}, b{dst, 7, 11, 12, 14, 80, 4};
    renderWindow(identity, a, b, 7, 11, 12, 14);
    assert(std::memcmp(src, dst, sizeof(src)) == 0);
    std::memset(dst, 0, sizeof(dst));
    ImageView negativePitch{dst + 40, 7, 11, 12, 14, -80, 4};
    renderWindow(identity, a, negativePitch, 7, 11, 12, 14);
    for (int row = 0; row < 3; row++)
        assert(std::memcmp(src + 20 * row, dst + 20 * (2 - row), 80) == 0);
    // Tile partitions must produce exactly the same output as one full render.
    src[0] = .1f;
    Snapshot exposure(Effect::Scene, {{"interpretation", 1}, {"exposure", 1.5}});
    float full[60];
    ImageView c{full, 7, 11, 12, 14, 80, 4};
    renderWindow(exposure, a, c, 7, 11, 12, 14);
    renderWindow(exposure, a, b, 7, 11, 9, 14);
    renderWindow(exposure, a, b, 9, 11, 12, 14);
    assert(std::memcmp(full, dst, sizeof(dst)) == 0);
    for (int i = 3; i < 60; i += 4)
        assert(dst[i] == src[i]);
    assert(a.at(12, 11) == nullptr && a.at(7, 14) == nullptr && a.at(6, 11) == nullptr);
    bool failed = false;
    try {
        renderWindow(identity, a, b, 6, 11, 12, 14);
    } catch (const std::invalid_argument &) {
        failed = true;
    }
    assert(failed);
    std::cout << "Native stride, bounds, tiles, alpha and exact identity checks passed\n";
}
