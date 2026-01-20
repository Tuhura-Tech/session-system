/**
 * Configuration for environment-specific settings
 */

export const config = {
  // Always call the API directly (no nginx proxy)
  apiUrl:
    (import.meta as any).env.PUBLIC_BASE_URL ||
    "https://sessions-api.tuhuratech.org.nz",
  appName: "Admin Portal",
  appVersion: "1.0.0",
};

// Feature flags
export const features = {
  attendance: true,
  exports: true,
  bulkEmail: true,
  waitlistPromotion: true,
  sessionBlocks: true,
  childNotes: true,
};
