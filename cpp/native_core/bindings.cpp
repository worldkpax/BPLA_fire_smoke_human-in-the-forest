#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "native_core.hpp"

namespace py = pybind11;

PYBIND11_MODULE(native_core, m) {
    m.doc() = "Native performance helpers for geo projection and energy estimation";

    m.def(
        "geo_distance_m",
        &geo_distance_m,
        py::arg("lat1_deg"),
        py::arg("lon1_deg"),
        py::arg("lat2_deg"),
        py::arg("lon2_deg"),
        R"pbdoc(
Great-circle distance in meters between two WGS84 points (degrees).
)pbdoc");

    m.def(
        "geo_distance_many",
        &geo_distance_many,
        py::arg("lats1"),
        py::arg("lons1"),
        py::arg("lats2"),
        py::arg("lons2"),
        R"pbdoc(
Vectorized great-circle distances (meters) for paired coordinates.
)pbdoc");

    m.def(
        "geo_project_bbox_to_ground",
        [](double lat_deg, double lon_deg, double alt_m, double yaw_rad, double pitch_rad, double roll_rad,
           double fx, double fy, double cx, double cy, double x_min, double y_min, double x_max, double y_max) {
            double out_lat = 0.0;
            double out_lon = 0.0;
            geo_project_bbox_to_ground(lat_deg, lon_deg, alt_m, yaw_rad, pitch_rad, roll_rad, fx, fy, cx, cy, x_min,
                                       y_min, x_max, y_max, &out_lat, &out_lon);
            return py::make_tuple(out_lat, out_lon);
        },
        py::arg("lat_deg"),
        py::arg("lon_deg"),
        py::arg("alt_m"),
        py::arg("yaw_rad"),
        py::arg("pitch_rad"),
        py::arg("roll_rad"),
        py::arg("fx"),
        py::arg("fy"),
        py::arg("cx"),
        py::arg("cy"),
        py::arg("x_min"),
        py::arg("y_min"),
        py::arg("x_max"),
        py::arg("y_max"),
        R"pbdoc(
Project bounding box center from image plane to ground coordinates.
Uses pinhole model + yaw/pitch/roll to cast a ray to ground plane (flat-earth).
)pbdoc");

    m.def(
        "offset_latlon",
        [](double lat_deg, double lon_deg, double dx_m, double dy_m) {
            double out_lat = 0.0, out_lon = 0.0;
            offset_latlon(lat_deg, lon_deg, dx_m, dy_m, &out_lat, &out_lon);
            return py::make_tuple(out_lat, out_lon);
        },
        py::arg("lat_deg"),
        py::arg("lon_deg"),
        py::arg("dx_m"),
        py::arg("dy_m"),
        R"pbdoc(
Offset a lat/lon point by local ENU displacements (meters).
)pbdoc");

    m.def(
        "route_length_m",
        [](const std::vector<double>& lats, const std::vector<double>& lons, const std::vector<double>& alts) {
            if (lats.size() != lons.size() || lats.size() != alts.size()) {
                throw py::value_error("route_length_m: vector sizes must match");
            }
            return route_length_m(lats, lons, alts);
        },
        py::arg("lats"),
        py::arg("lons"),
        py::arg("alts"),
        R"pbdoc(
Compute total route length (meters). Altitude is currently ignored.
)pbdoc");

    m.def(
        "route_energy_cost",
        [](const std::vector<double>& lats, const std::vector<double>& lons, const std::vector<double>& alts,
           double mass_kg, double base_power_w) {
            if (lats.size() != lons.size() || lats.size() != alts.size()) {
                throw py::value_error("route_energy_cost: vector sizes must match");
            }
            return route_energy_cost(lats, lons, alts, mass_kg, base_power_w);
        },
        py::arg("lats"),
        py::arg("lons"),
        py::arg("alts"),
        py::arg("mass_kg"),
        py::arg("base_power_w"),
        R"pbdoc(
Placeholder energy cost model proportional to distance, mass, and base power.
)pbdoc");

    py::class_<BBoxTracker>(m, "BBoxTracker")
        .def(
            py::init<double, double, double, double, int, int>(),
            py::arg("alpha") = 0.5,
            py::arg("max_center_distance_px") = 80.0,
            py::arg("iou_threshold") = 0.25,
            py::arg("max_age_seconds") = 2.0,
            py::arg("min_hits") = 2,
            py::arg("max_missed") = 10,
            R"pbdoc(
Lightweight IoU/center-based tracker with bbox smoothing.
)pbdoc")
        .def(
            "assign_and_smooth",
            [](BBoxTracker& self, py::sequence detections) {
                std::vector<DetectionInput> dets;
                dets.reserve(py::len(detections));
                for (auto item : detections) {
                    py::tuple t = py::cast<py::tuple>(item);
                    if (t.size() < 6) {
                        throw py::value_error("Detection tuple must be (class, conf, x1, y1, x2, y2, [ts])");
                    }
                    DetectionInput d;
                    d.class_id = py::cast<int>(t[0]);
                    d.confidence = py::cast<double>(t[1]);
                    d.x1 = py::cast<double>(t[2]);
                    d.y1 = py::cast<double>(t[3]);
                    d.x2 = py::cast<double>(t[4]);
                    d.y2 = py::cast<double>(t[5]);
                    d.timestamp = (t.size() >= 7) ? py::cast<double>(t[6]) : 0.0;
                    dets.push_back(d);
                }
                py::list out;
                for (const auto& res : self.assign_and_smooth(dets)) {
                    out.append(py::make_tuple(res.det_index, res.track_id, py::make_tuple(res.x1, res.y1, res.x2, res.y2)));
                }
                return out;
            },
            py::arg("detections"),
            R"pbdoc(
Assign detections to tracks and smooth bboxes.
Input: list of tuples (class_id, confidence, x1, y1, x2, y2[, timestamp_seconds]).
Returns list of tuples (det_index, track_id, (x1,y1,x2,y2)).
)pbdoc",
            py::call_guard<py::gil_scoped_release>());
}
