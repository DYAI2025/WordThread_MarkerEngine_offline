// ======================================================================
// GR_timestamp-plugin.js   –   Lean-Deep 3.2-ready (v2.0.0)
// ======================================================================

import { MarkerPlugin } from '../packages/cli/src/plugin-api.js';

/**
 * Timestamp-Plugin
 *  • fügt Validierungs- und Batch-Zeitstempel in `x_…`-Felder ein
 *  • keine Schema-Kollision dank `additionalProperties`
 */

export default class TimestampPlugin extends MarkerPlugin {
  constructor() {
    super();
    this.name        = 'timestamp';
    this.version     = '2.0.0';
    this.description = 'Adds processing timestamps to markers';
  }

  async init(ctx) {
    ctx.log('Timestamp-Plugin initialised');
    this.start = Date.now();
  }

  async beforeValidation(marker) {
    marker.x_validated_at = new Date().toISOString();
    return marker;
  }

  async beforeRepair(marker) {
    marker.x_repair_started = new Date().toISOString();
    return marker;
  }

  async afterRepair(marker) {
    marker.x_repair_finished = new Date().toISOString();
    return marker;
  }

  async afterBatch(results, ctx) {
    const dur = (Date.now() - this.start) / 1000;
    ctx.log(`Batch in ${dur.toFixed(2)} s; ${results.length} Marker verarbeitet`);
    ctx.setMetadata('batch_duration_sec', dur);
  }
}
