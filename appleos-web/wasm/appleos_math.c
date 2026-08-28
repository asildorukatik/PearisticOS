// Tiny AppleOS numeric hot-path module. No libc is required.

static double clamp01(double x) {
    if (x < 0.0) return 0.0;
    if (x > 1.0) return 1.0;
    return x;
}

static double cos_approx(double x) {
    const double PI = 3.14159265358979323846;
    const double TAU = 6.28318530717958647692;
    while (x > PI) x -= TAU;
    while (x < -PI) x += TAU;
    const double x2 = x * x;
    const double x4 = x2 * x2;
    const double x6 = x4 * x2;
    const double x8 = x4 * x4;
    return 1.0 - x2 / 2.0 + x4 / 24.0 - x6 / 720.0 + x8 / 40320.0;
}

__attribute__((export_name("cosine_magnification01")))
double cosine_magnification01(double normalized) {
    const double TAU = 6.28318530717958647692;
    const double n = clamp01(normalized);
    double factor = (1.0 - cos_approx(n * TAU)) * 0.5;
    return clamp01(factor);
}

__attribute__((export_name("spring_step")))
double spring_step(double current, double target, double velocity, double stiffness, double damping, double dt) {
    const double acceleration = (target - current) * stiffness - velocity * damping;
    const double next_velocity = velocity + acceleration * dt;
    return current + next_velocity * dt;
}
