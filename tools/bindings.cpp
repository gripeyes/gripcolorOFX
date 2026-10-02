#include "rendition/diagnostics.hpp"
#include "rendition/operators.hpp"
#include "rendition/artist_models.hpp"
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;
using namespace rendition;
PYBIND11_MODULE(_rendition, m) {
    m.def("local_exposure",[](std::array<float,4> rgba,float coverage,const Values &v){return localExposure(Snapshot(Effect::Base,v),rgba,coverage);});
    m.def("encode", [](float x, int d) { return encode(x, static_cast<LookDomain>(d)); });
    m.def("decode", [](float x, int d) { return decode(x, static_cast<LookDomain>(d)); });
    m.def("matrix", [](int g) { return ColorSpace::make(static_cast<Gamut>(g)).toXYZ.v; });
    m.def("adaptation", [](double sx, double sy, double dx, double dy, int method) {
        return adaptation(sx, sy, dx, dy, method).v;
    });
    m.def("interpret", [](int manual, std::string tag) { return interpret(manual, tag).toXYZ.v; });
    m.def("roundtrip", [](std::array<float, 3> v, int g) {
        auto s = ColorSpace::make(static_cast<Gamut>(g));
        auto a = s.fromXYZ * (s.toXYZ * Vec3{v[0], v[1], v[2]});
        return std::array<float, 3>{a.x, a.y, a.z};
    });
    m.def("parameters", [](int e) {
        py::list result;
        for (auto &p : parameters(static_cast<Effect>(e))) {
            py::dict d;
            d["id"] = p.id;
            d["label"] = p.label;
            d["group"] = p.group;
            d["unit"] = p.unit;
            d["default"] = p.value;
            d["min"] = p.lo;
            d["max"] = p.hi;
            d["choices"] = p.choices;
            result.append(d);
        }
        return result;
    });
    m.def(
        "semantics",
        [](int e, const Values &v) {
            auto s = semantics(static_cast<Effect>(e), v);
            py::dict d;
            d["domain"] = s.domain;
            d["reference"] = s.reference;
            d["exposure"] = s.exposure;
            d["invertibility"] = s.invertibility;
            d["gamut"] = s.gamut;
            d["negative"] = s.negative;
            d["hdr"] = s.hdr;
            d["neutral_axis"] = s.neutralAxis;
            d["neutral_magnitude"] = s.neutralMagnitude;
            d["gamut_dependence"] = s.gamutDependence;
            d["status"] = s.status;
            d["limitations"] = s.limitations;
            return d;
        },
        py::arg("effect"), py::arg("values") = Values{});
    m.def(
        "process",
        [](int e, py::array_t<float, py::array::c_style | py::array::forcecast> image, const Values &p,
           const std::string &tag) {
            auto b = image.request();
            if (b.ndim < 1 || b.shape.back() != 4)
                throw std::invalid_argument("Expected (...,4) float RGBA");
            Snapshot snap(static_cast<Effect>(e), p, tag);
            py::array_t<float> out(b.shape);
            auto dst = out.mutable_data();
            auto src = static_cast<const float *>(b.ptr);
            {
                py::gil_scoped_release release;
                for (ptrdiff_t i = 0; i < b.size / 4; i++) {
                    auto q = snap.pixel({src[4 * i], src[4 * i + 1], src[4 * i + 2], src[4 * i + 3]});
                    for (int j = 0; j < 4; j++)
                        dst[4 * i + j] = q[j];
                }
            }
            return out;
        },
        py::arg("effect"), py::arg("rgba"), py::arg("values") = Values{}, py::arg("metadata") = "");
    m.def("opponent", [](std::array<float, 3> v, bool inverse) {
        Vec3 x{v[0], v[1], v[2]};
        x = inverse ? oklabInverse(x) : oklab(x);
        return std::array<float, 3>{x.x, x.y, x.z};
    });
    m.def("differentials", [](int e,py::array_t<float,py::array::c_style|py::array::forcecast> samples,const Values &p,double step) {
        auto b=samples.request();if(b.ndim!=2 || b.shape[1]!=3) throw std::invalid_argument("Expected Nx3 RGB");
        Snapshot snapshot(static_cast<Effect>(e),p);py::array_t<double> output({b.shape[0],py::ssize_t(16)});
        const float *src=static_cast<const float *>(b.ptr);double *dst=output.mutable_data();
        {py::gil_scoped_release release;for(py::ssize_t n=0;n<b.shape[0];++n) {
            auto d=differential(snapshot,{src[n*3],src[n*3+1],src[n*3+2]},step);
            for(int k=0;k<9;++k) dst[n*16+k]=d.jacobian.v[k];
            dst[n*16+9]=d.determinant;for(int k=0;k<3;++k)dst[n*16+10+k]=d.singularValues[k];
            dst[n*16+13]=d.condition;dst[n*16+14]=d.stepDisagreement;dst[n*16+15]=d.reliable;
        }}return output;
    },py::arg("effect"),py::arg("rgb"),py::arg("values"),py::arg("relative_step")=.002);
    m.def("effective_matrix",
          [](int e, const Values &p) { return Snapshot(static_cast<Effect>(e), p).effectiveMatrix().v; });
}
