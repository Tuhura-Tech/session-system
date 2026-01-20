/**
 * Configuration for environment-specific settings
 */

export const config = {
  apiUrl: (import.meta as any).env.VITE_API_URL || "http://localhost:8000",
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
