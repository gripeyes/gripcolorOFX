#pragma once
#include "operators.hpp"
namespace rendition {
std::vector<Parameter> artistParameters(Effect effect);
Values baseValues(const Values &values);
std::vector<std::pair<Effect, Values>> artistStages(Effect effect, const Values &values);
// Matte is an explicitly bounded alpha coverage; no image segmentation here.
std::array<float,4> localExposure(const Snapshot &base, std::array<float,4> pixel, float coverage);
}
