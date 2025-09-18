// ======================================================================
// GR_kimi-suggest-plugin.js   –   Lean-Deep 3.2-ready (v2.0.0)
// ======================================================================

import { MarkerPlugin } from '../packages/cli/src/plugin-api.js';

/**
 * Kimi-Suggest - ergänzt Tags anhand einfacher Keyword-Heuristik.
 * 3.2-Änderungen:
 *   • Präfix-Validierung (ATO_/SEM_/CLU_/MEMA_)
 *   • Level-Tagging via Präfix statt numerischem level-Feld
 *   • Alle neuen Tags landen in marker.x_suggested_tags (Zusatzfeld erlaubt)
 */

export default class KimiSuggestPlugin extends MarkerPlugin {
  constructor() {
    super();
    this.name        = 'kimi-suggest';
    this.version     = '2.0.0';
    this.description = 'Suggests additional tags based on marker content';

    // Keyword → Tag-Liste
    this.keywordMap = {
      password: ['security', 'authentication', 'credentials'],
      token:    ['security', 'authentication', 'api'],
      encrypt:  ['security', 'cryptography'],
      decrypt:  ['security', 'cryptography'],
      auth:     ['authentication', 'security'],
      login:    ['authentication', 'user-session'],
      logout:   ['authentication', 'user-session'],

      database: ['data-storage', 'persistence'],
      cache:    ['performance', 'data-storage'],
      backup:   ['data-protection', 'recovery'],

      email:  ['communication', 'notification'],
      sms:    ['communication', 'notification'],
      api:    ['integration', 'interface'],

      optimize: ['performance', 'efficiency'],
      slow:     ['performance', 'issue'],
      bug:      ['issue', 'defect'],

      fraud: ['security', 'risk', 'fraud'],
      fake:  ['fraud', 'deception']
    };
  }

  async init(ctx) {
    ctx.log('Kimi-Suggest Plugin initialised');
    ctx.setMetadata('suggestions_count', 0);
  }

  async afterValidation(marker, validationResult, ctx) {
    if (!validationResult.valid) return;

    // 1) Textbasis
    const baseText = [
      marker.marker ?? '',
      marker.description ?? '',
      ...(marker.examples ?? [])
    ].join(' ').toLowerCase();

    const tagSet = new Set(marker.tags ?? []);
    const originalSize = tagSet.size;

    // 2) Keyword-Analyse
    Object.entries(this.keywordMap).forEach(([kw, tags]) => {
      if (baseText.includes(kw)) tags.forEach(t => tagSet.add(t));
    });

    // 3) Ebene über Präfix ableiten
    const prefix = (marker.id ?? '').slice(0, 4);
    if (['ATO_','SEM_','CLU_','MEMA_'].includes(prefix))
      tagSet.add(
        { ATO_: 'atomic', SEM_: 'semantic', CLU_: 'cluster', MEMA_: 'meta' }[prefix]
      );

    // 4) Risiko-Tags
    if ((marker.scoring?.base ?? 0) * (marker.scoring?.weight ?? 1) >= 4)
      tagSet.add('high-risk');

    // 5) Ergebnis speichern
    const newTags = [...tagSet];
    const added = newTags.length - originalSize;
    if (added) {
      marker.x_suggested_tags = newTags.filter(t => !(marker.tags ?? []).includes(t));
      ctx.setMetadata('suggestions_count', ctx.getMetadata('suggestions_count') + added);
      ctx.log(`Kimi-Suggest: +${added} Tag(s) für ${marker.id}`);
    }
  }

  async afterBatch(res, ctx) {
    const n = ctx.getMetadata('suggestions_count');
    if (n) ctx.log(`Kimi-Suggest gesamt: ${n} neue Tag-Vorschläge`);
  }
}
