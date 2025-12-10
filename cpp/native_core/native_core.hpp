#pragma once

#include <vector>

// Geodesic distance between two WGS84 points (degrees) using haversine, meters.
double geo_distance_m(double lat1_deg, double lon1_deg, double lat2_deg, double lon2_deg);

// Project bounding box center from image plane to ground lat/lon.
void geo_project_bbox_to_ground(
    double lat_deg, double lon_deg, double alt_m,
    double yaw_rad, double pitch_rad, double roll_rad,
    double fx, double fy, double cx, double cy,
    double x_min, double y_min, double x_max, double y_max,
    double* out_lat_center_deg,
    double* out_lon_center_deg);

// Offset lat/lon by local ENU displacements (meters).
void offset_latlon(double lat_deg, double lon_deg, double dx_m, double dy_m,
                   double* out_lat_deg, double* out_lon_deg);

// Compute per-element distances (meters) for paired lat/lon vectors; sizes must match.
std::vector<double> geo_distance_many(const std::vector<double>& lats1_deg,
                                      const std::vector<double>& lons1_deg,
                                      const std::vector<double>& lats2_deg,
                                      const std::vector<double>& lons2_deg);

// Compute total route length (meters) given waypoint lat/lon/alt vectors.
// Throws std::invalid_argument if vector sizes mismatch. Altitude is currently ignored.
double route_length_m(const std::vector<double>& lats_deg,
                      const std::vector<double>& lons_deg,
                      const std::vector<double>& alts_m);

// Placeholder energy cost model for a route.
// Throws std::invalid_argument on size mismatch.
double route_energy_cost(const std::vector<double>& lats_deg,
                         const std::vector<double>& lons_deg,
                         const std::vector<double>& alts_m,
                         double mass_kg,
                         double base_power_w);

// ───────────── Tracking / smoothing ─────────────
struct DetectionInput {
    int class_id;
    double confidence;
    double x1, y1, x2, y2;
    double timestamp;
};

struct AssignResult {
    double x1, y1, x2, y2;
    int track_id;
    int det_index;
};

class BBoxTracker {
public:
    BBoxTracker(double alpha,
                double max_center_distance_px,
                double iou_threshold,
                double max_age_seconds,
                int min_hits,
                int max_missed);

    std::vector<AssignResult> assign_and_smooth(const std::vector<DetectionInput>& detections);

private:
    struct TrackState {
        double x1, y1, x2, y2;
        int track_id;
        int class_id;
        double score;
        int hits;
        int missed;
        double last_seen;
    };

    double alpha_;
    double max_center_distance_;
    double iou_threshold_;
    double max_age_seconds_;
    int min_hits_;
    int max_missed_;
    int next_track_id_;
    std::vector<TrackState> tracks_;

    static double iou(const TrackState& t, double x1, double y1, double x2, double y2);
    static double center_sim(const TrackState& t, double x1, double y1, double x2, double y2, double max_center_dist);
    void prune(double now);
};
