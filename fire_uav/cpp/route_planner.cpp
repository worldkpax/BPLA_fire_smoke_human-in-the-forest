// route_planner.cpp  — C++-ускоритель планировщика
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;

struct Waypoint {
    double lat;
    double lon;
    double alt;
};

static constexpr double kEarthRadiusM = 6378137.0;

// --- util: deg→m и обратно (эквирект.) ------------------------------------
struct Vec2 { double x, y; };

static Vec2 geo2m(double lat0, double lon0, double lat, double lon)
{
    double dLat = (lat - lat0) * M_PI / 180.0;
    double dLon = (lon - lon0) * M_PI / 180.0;
    double x = dLon * kEarthRadiusM * std::cos(lat0 * M_PI / 180.0);
    double y = dLat * kEarthRadiusM;
    return {x, y};
}

static std::pair<double,double> m2geo(double lat0, double lon0, Vec2 v)
{
    double dLat = v.y / kEarthRadiusM;
    double dLon = v.x / (kEarthRadiusM * std::cos(lat0 * M_PI / 180.0));
    return {lat0 + dLat*180.0/M_PI, lon0 + dLon*180.0/M_PI};
}

// ---------------------------------------------------------------------------
// 1. «Змейка» (lawn-mower) по bbox полигона
// ---------------------------------------------------------------------------
std::vector<Waypoint> generate_lawnmower(
        const std::vector<std::pair<double,double>>& poly_latlon,
        double swath_m,
        double altitude_m)
{
    if (poly_latlon.size() < 3)
        throw std::runtime_error("Polygon must have ≥3 vertices");

    double lat0 = poly_latlon[0].first;
    double lon0 = poly_latlon[0].second;

    std::vector<Vec2> verts;
    verts.reserve(poly_latlon.size());
    for (auto& p : poly_latlon)
        verts.push_back( geo2m(lat0, lon0, p.first, p.second) );

    double xmin=1e9,xmax=-1e9,ymin=1e9,ymax=-1e9;
    for (auto& v : verts){
        xmin = std::min(xmin, v.x); xmax = std::max(xmax, v.x);
        ymin = std::min(ymin, v.y); ymax = std::max(ymax, v.y);
    }

    std::vector<Waypoint> out;
    bool left2right = true;
    for (double y = ymin; y <= ymax; y += swath_m) {
        Vec2 a{ xmin, y }, b{ xmax, y };
        if (!left2right) std::swap(a, b);
        left2right = !left2right;
        for (Vec2 v : {a, b}) {
            auto [lat, lon] = m2geo(lat0, lon0, v);
            out.push_back({lat, lon, altitude_m});
        }
    }
    return out;
}

// ---------------------------------------------------------------------------
// 2. «Следовать по пути» — копия пользовательской ломаной
// ---------------------------------------------------------------------------
std::vector<Waypoint> follow_path(
        const std::vector<std::pair<double,double>>& path_latlon,
        double altitude_m)
{
    std::vector<Waypoint> out;
    out.reserve(path_latlon.size());
    for (auto& p : path_latlon)
        out.push_back({p.first, p.second, altitude_m});
    return out;
}

// ---------------------------------------------------------------------------
// PYBIND11 ЭКСПОРТ
// ---------------------------------------------------------------------------
PYBIND11_MODULE(route_planner_cpp, m) {
    py::class_<Waypoint>(m, "Waypoint")
        .def(py::init<>())
        .def_readwrite("lat", &Waypoint::lat)
        .def_readwrite("lon", &Waypoint::lon)
        .def_readwrite("alt", &Waypoint::alt);

    m.def("generate_route", &generate_lawnmower,
          py::arg("polygon_latlon"),
          py::arg("swath_m"),
          py::arg("altitude_m") = 120.0,
          "Lawn-mower route for given polygon (bbox)",
          py::call_guard<py::gil_scoped_release>());

    m.def("follow_path", &follow_path,
          py::arg("path_latlon"),
          py::arg("altitude_m") = 120.0,
          "Return WP exactly along given polyline",
          py::call_guard<py::gil_scoped_release>());
}
