// ======================================================================
// GR_sample-plugin.js   –   Plugin API v2 (Lean-Deep 3.2 kompatibel)
// ======================================================================

/**
 * Sample Plugin – demonstriert neue 3.2-Hook-Namen + Prefix-Check.
 */
export const plugin = {
  name:        "sample-plugin",
  version:     "2.0.0",
  description: "Adds tag statistics & 4-prefix validation",

  async init(ctx) {
    console.log(`${this.name} v${this.version} loaded`);
    this.tagStats = new Map();
  },

  /* ---- HOOKS ------------------------------------------------------ */

  async beforeValidation(marker, ctx) {
    // 4-Letter-Prefix prüfen (ATO_/SEM_/CLU_/MEMA_)
    if (!/^(ATO|SEM|CLU|MEMA)_/.test(marker.id)) {
      marker.validationErrors = marker.validationErrors ?? [];
      marker.validationErrors.push("E_PREFIX");
    }

    // Tag-Statistik
    (marker.tags ?? []).forEach(tag =>
      this.tagStats.set(tag, (this.tagStats.get(tag) || 0) + 1)
    );
    return marker;
  },

  async afterValidation(marker, result, ctx) {
    if (result.valid && marker.tags?.includes("high-priority")) {
      result.pluginNotes = { priority: "HIGH" };
    }
    return result;
  },

  async beforeRepair(marker, ctx) {
    // Auto-Category-Vorschlag
    if (!marker.category && marker.tags?.length)
      marker.suggested_category = marker.tags[0].toUpperCase();
    return marker;
  },

  async afterBatch(batchResult, ctx) {
    const report = {
      totalTags : this.tagStats.size,
      topTags   : [...this.tagStats.entries()]
                    .sort((a,b)=>b[1]-a[1]).slice(0,10)
    };
    return {
      ...batchResult,
      pluginReports: { ...batchResult.pluginReports, [this.name]: report }
    };
  }
};

export default plugin;
