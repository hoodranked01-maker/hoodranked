// HOODRANKED analytics — thin wrapper around GA4's gtag().
// Load this AFTER the GA4 base snippet (in base.html <head>) and BEFORE any
// page script that calls trackEvent(...), e.g. product-detail.js.

window.trackEvent = function (eventName, params = {}) {
  if (typeof window.gtag === "function") {
    window.gtag("event", eventName, params);
  } else {
    // gtag not loaded yet (blocked by an ad blocker, slow network, etc.) —
    // log it instead of throwing, so pages that call trackEvent still work.
    console.warn(`trackEvent("${eventName}") skipped — gtag not available`, params);
  }
};