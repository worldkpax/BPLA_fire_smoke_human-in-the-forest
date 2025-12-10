#include "native_core.hpp"

#include <algorithm>
#include <cmath>
#include <chrono>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace {
constexpr double kEarthRadiusM = 6'371'000.0;  // meters
constexpr double kPi = 3.14159265358979323846;

inline double deg2rad(double deg) {
    return deg * kPi / 180.0;
}

inline double rad2deg(double rad) {
    return rad * 180.0 / kPi;
}
}  // namespace

double geo_distance_m(double lat1_deg, double lon1_deg, double lat2_deg, double lon2_deg) {
    // Haversine great-circle distance.
    const double lat1 = deg2rad(lat1_deg);
    const double lat2 = deg2rad(lat2_deg);
    const double dlat = lat2 - lat1;
    const double dlon = deg2rad(lon2_deg - lon1_deg);

    const double a = std::sin(dlat / 2) * std::sin(dlat / 2) +
                     std::cos(lat1) * std::cos(lat2) * std::sin(dlon / 2) * std::sin(dlon / 2);
    const double c = 2 * std::asin(std::min(1.0, std::sqrt(a)));
    return kEarthRadiusM * c;
}

void geo_project_bbox_to_ground(
    double lat_deg, double lon_deg, double alt_m,
    double yaw_rad, double pitch_rad, double roll_rad,
    double fx, double fy, double cx, double cy,
    double x_min, double y_min, double x_max, double y_max,
    double* out_lat_center_deg,
    double* out_lon_center_deg) {
    // Pinhole model + flat earth: cast a ray from camera through bbox center and
    // intersect with ground plane z=0 (alt_m above ground). Assumes camera frame
    // has +X right, +Y down, +Z forward.
    const double u = (x_min + x_max) * 0.5;
    const double v = (y_min + y_max) * 0.5;
    // Guard intrinsics to avoid division by zero.
    fx = (fx == 0.0) ? 1.0 : fx;
    fy = (fy == 0.0) ? 1.0 : fy;
    const double x_cam = (u - cx) / fx;
    const double y_cam = (v - cy) / fy;
    // Ray in camera frame.
    const double dir_cam[3] = {x_cam, y_cam, 1.0};

    // Rotation Z (yaw) * Y (pitch) * X (roll) -> world (ENU-ish).
    const double cyaw = std::cos(yaw_rad), syaw = std::sin(yaw_rad);
    const double cpitch = std::cos(pitch_rad), spitch = std::sin(pitch_rad);
    const double croll = std::cos(roll_rad), sroll = std::sin(roll_rad);

    const double r00 = cyaw * cpitch;
    const double r01 = cyaw * spitch * sroll - syaw * croll;
    const double r02 = cyaw * spitch * croll + syaw * sroll;
    const double r10 = syaw * cpitch;
    const double r11 = syaw * spitch * sroll + cyaw * croll;
    const double r12 = syaw * spitch * croll - cyaw * sroll;
    const double r20 = -spitch;
    const double r21 = cpitch * sroll;
    const double r22 = cpitch * croll;

    const double dx = r00 * dir_cam[0] + r01 * dir_cam[1] + r02 * dir_cam[2];
    const double dy = r10 * dir_cam[0] + r11 * dir_cam[1] + r12 * dir_cam[2];
    const double dz = r20 * dir_cam[0] + r21 * dir_cam[1] + r22 * dir_cam[2];

    // Intersect with ground plane z=0 from origin at (0,0,alt_m).
    double out_lat = lat_deg;
    double out_lon = lon_deg;
    if (std::abs(dz) > 1e-6) {
        const double t = -alt_m / dz;  // step along ray
        const double gx = t * dx;
        const double gy = t * dy;
        offset_latlon(lat_deg, lon_deg, gx, gy, &out_lat, &out_lon);
    }

    if (out_lat_center_deg) {
        *out_lat_center_deg = out_lat;
    }
    if (out_lon_center_deg) {
        *out_lon_center_deg = out_lon;
    }
}

void offset_latlon(double lat_deg, double lon_deg, double dx_m, double dy_m,
                   double* out_lat_deg, double* out_lon_deg) {
    // ENU approximation.
    const double d_lat = dy_m / kEarthRadiusM;
    const double d_lon = dx_m / (kEarthRadiusM * std::cos(deg2rad(lat_deg)));
    if (out_lat_deg) {
        *out_lat_deg = lat_deg + rad2deg(d_lat);
    }
    if (out_lon_deg) {
        *out_lon_deg = lon_deg + rad2deg(d_lon);
    }
}

std::vector<double> geo_distance_many(const std::vector<double>& lats1_deg,
                                      const std::vector<double>& lons1_deg,
                                      const std::vector<double>& lats2_deg,
                                      const std::vector<double>& lons2_deg) {
    const size_t n = lats1_deg.size();
    if (lons1_deg.size() != n || lats2_deg.size() != n || lons2_deg.size() != n) {
        throw std::invalid_argument("geo_distance_many: vector sizes must match");
    }
    std::vector<double> out;
    out.reserve(n);
    for (size_t i = 0; i < n; ++i) {
        out.push_back(geo_distance_m(lats1_deg[i], lons1_deg[i], lats2_deg[i], lons2_deg[i]));
    }
    return out;
}

double route_length_m(const std::vector<double>& lats_deg,
                      const std::vector<double>& lons_deg,
                      const std::vector<double>& alts_m) {
    if (lats_deg.size() != lons_deg.size() || lats_deg.size() != alts_m.size()) {
        throw std::invalid_argument("route_length_m: vector sizes must match");
    }
    if (lats_deg.size() < 2) {
        return 0.0;
    }

    double total = 0.0;
    for (size_t i = 1; i < lats_deg.size(); ++i) {
        total += geo_distance_m(lats_deg[i - 1], lons_deg[i - 1], lats_deg[i], lons_deg[i]);
    }
    // Altitude change ignored in distance; acceptable for placeholder.
    return total;
}

double route_energy_cost(const std::vector<double>& lats_deg,
                         const std::vector<double>& lons_deg,
                         const std::vector<double>& alts_m,
                         double mass_kg,
                         double base_power_w) {
    if (lats_deg.size() != lons_deg.size() || lats_deg.size() != alts_m.size()) {
        throw std::invalid_argument("route_energy_cost: vector sizes must match");
    }
    const double length_m = route_length_m(lats_deg, lons_deg, alts_m);
    // Placeholder model; refine with aerodynamics/drag as needed.
    const double energy = length_m * mass_kg * base_power_w * 1e-3;
    return energy;
}

// ───────────── Tracking / smoothing ─────────────
BBoxTracker::BBoxTracker(double alpha,
                         double max_center_distance_px,
                         double iou_threshold,
                         double max_age_seconds,
                         int min_hits,
                         int max_missed)
    : alpha_(alpha),
      max_center_distance_(max_center_distance_px),
      iou_threshold_(iou_threshold),
      max_age_seconds_(max_age_seconds),
      min_hits_(min_hits),
      max_missed_(max_missed),
      next_track_id_(0) {}

double BBoxTracker::iou(const TrackState& t, double x1, double y1, double x2, double y2) {
    const double inter_x1 = std::max(t.x1, x1);
    const double inter_y1 = std::max(t.y1, y1);
    const double inter_x2 = std::min(t.x2, x2);
    const double inter_y2 = std::min(t.y2, y2);
    const double inter_w = std::max(0.0, inter_x2 - inter_x1);
    const double inter_h = std::max(0.0, inter_y2 - inter_y1);
    const double inter_area = inter_w * inter_h;
    if (inter_area <= 0.0) {
        return 0.0;
    }
    const double area_a = std::max(0.0, t.x2 - t.x1) * std::max(0.0, t.y2 - t.y1);
    const double area_b = std::max(0.0, x2 - x1) * std::max(0.0, y2 - y1);
    const double uni = area_a + area_b - inter_area;
    return (uni > 0.0) ? (inter_area / uni) : 0.0;
}

double BBoxTracker::center_sim(const TrackState& t,
                               double x1,
                               double y1,
                               double x2,
                               double y2,
                               double max_center_dist) {
    if (max_center_dist <= 0.0) {
        return 0.0;
    }
    const double ax = (t.x1 + t.x2) * 0.5;
    const double ay = (t.y1 + t.y2) * 0.5;
    const double bx = (x1 + x2) * 0.5;
    const double by = (y1 + y2) * 0.5;
    const double dx = ax - bx;
    const double dy = ay - by;
    const double dist = std::sqrt(dx * dx + dy * dy);
    if (dist > max_center_dist) {
        return 0.0;
    }
    return std::max(0.0, 1.0 - dist / max_center_dist);
}

void BBoxTracker::prune(double now) {
    std::vector<TrackState> kept;
    kept.reserve(tracks_.size());
    for (auto& t : tracks_) {
        const int max_missed = (t.hits >= min_hits_) ? max_missed_ : std::min(2, max_missed_);
        if ((now - t.last_seen) > max_age_seconds_ || t.missed > max_missed) {
            continue;
        }
        kept.push_back(t);
    }
    tracks_.swap(kept);
}

std::vector<AssignResult> BBoxTracker::assign_and_smooth(const std::vector<DetectionInput>& detections) {
    using Clock = std::chrono::steady_clock;
    const double now = std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
    if (detections.empty()) {
        prune(now);
        return {};
    }

    // Build candidate list (score, track_idx, det_idx).
    std::vector<std::tuple<double, size_t, size_t>> candidates;
    for (size_t ti = 0; ti < tracks_.size(); ++ti) {
        const auto& t = tracks_[ti];
        for (size_t di = 0; di < detections.size(); ++di) {
            const auto& d = detections[di];
            if (d.class_id != t.class_id) {
                continue;
            }
            const double i = iou(t, d.x1, d.y1, d.x2, d.y2);
            const double c = center_sim(t, d.x1, d.y1, d.x2, d.y2, max_center_distance_);
            if (i < iou_threshold_ && c <= 0.0) {
                continue;
            }
            const double score = (i >= iou_threshold_) ? i : (0.001 + 0.2 * c);
            candidates.emplace_back(score, ti, di);
        }
    }
    std::sort(candidates.begin(), candidates.end(),
              [](const auto& a, const auto& b) { return std::get<0>(a) > std::get<0>(b); });

    std::vector<int> det_assigned(detections.size(), -1);  // track idx
    std::vector<bool> track_used(tracks_.size(), false);
    std::vector<AssignResult> results;
    results.reserve(detections.size());

    // Greedy assign.
    for (const auto& cand : candidates) {
        const size_t ti = std::get<1>(cand);
        const size_t di = std::get<2>(cand);
        if (track_used[ti] || det_assigned[di] != -1) {
            continue;
        }
        auto& t = tracks_[ti];
        const auto& d = detections[di];
        // Smooth bbox.
        t.x1 = alpha_ * d.x1 + (1.0 - alpha_) * t.x1;
        t.y1 = alpha_ * d.y1 + (1.0 - alpha_) * t.y1;
        t.x2 = alpha_ * d.x2 + (1.0 - alpha_) * t.x2;
        t.y2 = alpha_ * d.y2 + (1.0 - alpha_) * t.y2;
        t.score = d.confidence;
        t.hits += 1;
        t.missed = 0;
        t.last_seen = (d.timestamp > 0.0) ? d.timestamp : now;
        det_assigned[di] = static_cast<int>(ti);
        track_used[ti] = true;
        results.push_back({t.x1, t.y1, t.x2, t.y2, t.track_id, static_cast<int>(di)});
    }

    // Create tracks for unassigned detections.
    for (size_t di = 0; di < detections.size(); ++di) {
        if (det_assigned[di] != -1) {
            continue;
        }
        const auto& d = detections[di];
        TrackState t{d.x1, d.y1, d.x2, d.y2, next_track_id_++, d.class_id, d.confidence, 1, 0,
                     (d.timestamp > 0.0) ? d.timestamp : now};
        tracks_.push_back(t);
        results.push_back({d.x1, d.y1, d.x2, d.y2, t.track_id, static_cast<int>(di)});
    }

    // Increment missed for unused tracks.
    track_used.resize(tracks_.size(), false);
    for (size_t ti = 0; ti < tracks_.size(); ++ti) {
        if (!track_used[ti]) {
            tracks_[ti].missed += 1;
        }
    }

    prune(now);
    std::sort(results.begin(), results.end(),
              [](const AssignResult& a, const AssignResult& b) { return a.det_index < b.det_index; });
    return results;
}
