import { LitElement, html, css } from 'https://unpkg.com/lit-element?module';

class FroniusSmartmeterIPCard extends LitElement {
  static get type() {
    return 'fronius-smartmeter-ip-card';
  }

  static get name() {
    return 'Fronius Smartmeter Phasenplot (Konfigurierbare Entitäten)';
  }

  static get description() {
    return 'Visualisiert Spannungs- und Stromphasenvektoren für einen Smart Meter mit individuell konfigurierbaren Entitäten.';
  }

  static get preview() {
    return true;
  }

  static getLovelaceConfig() {
    return {
      type: this.type,
    };
  }

  static get properties() {
    return {
      hass: Object,
      config: Object,
    };
  }

  static get styles() {
    return css`
        :host {
            display: block;
            /* Standard-Fallback-Farben definieren, falls Variablen nicht gesetzt sind (optional, aber gut) */
            --color-l1: #e14621;
            --color-l2: green;
            --color-l3: #1E90FF;
            --color-n: #000000;
        }
        ha-card {
            overflow: hidden;
        }
        .card-content {
            padding: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        svg#diagram {
            width: 100%;
            max-width: 340px;
            height: auto;
        }
        .plottext {
            font-size: 12pt;
            fill: #777777; /* Allgemeine Achsenbeschriftungen bleiben grau */
        }
        .legend {
            font-size: 10pt;
            fill: var(--secondary-text-color); /* Legendentext bleibt Standard */
        }

        /* Farben für Achsen-Skalierungstexte (Spannung/Strom-Maximalwerte) */
        /* Diese können generisch bleiben oder auch angepasst werden, falls gewünscht */
        text.voltage { /* z.B. +230V Text */
            fill: #e14621; /* Behält aktuelle generische Farbe für Achsenbeschriftungen */
        }
        text.current { /* z.B. +1A Text */
            fill: #1E90FF; /* Behält aktuelle generische Farbe für Achsenbeschriftungen */
        }

        /* Pfeilspitzen (Marker) Farben über CSS Variablen */
        marker#arrowheadA path { fill: var(--color-l1); }
        marker#arrowheadB path { fill: var(--color-l2); }
        marker#arrowheadC path { fill: var(--color-l3); }
        marker#arrowheadN path { fill: var(--color-n); }

        /* Vektorlinien Farben über CSS Variablen */
        /* Spannungsvektoren */
        line#arrowVA { stroke: var(--color-l1); stroke-width: 1.5; stroke-dasharray: 2; }
        line#arrowVB { stroke: var(--color-l2); stroke-width: 1.5; stroke-dasharray: 2; }
        line#arrowVC { stroke: var(--color-l3); stroke-width: 1.5; stroke-dasharray: 2; }

        /* Stromvektoren */
        line#arrowIA { stroke: var(--color-l1); stroke-width: 1.5; stroke-dasharray: 5; }
        line#arrowIB { stroke: var(--color-l2); stroke-width: 1.5; stroke-dasharray: 5; }
        line#arrowIC { stroke: var(--color-l3); stroke-width: 1.5; stroke-dasharray: 5; }
        line#arrowIN { stroke: var(--color-n); stroke-width: 1.5; stroke-dasharray: 5; }

        /* Legenden-Linien Farben */
        line.legend-line.phase-a { stroke: var(--color-l1); stroke-width: 1.5; }
        line.legend-line.phase-b { stroke: var(--color-l2); stroke-width: 1.5; }
        line.legend-line.phase-c { stroke: var(--color-l3); stroke-width: 1.5; }
        /* Ggf. Strichart für Legende anpassen, falls gewünscht */

    `;
  }

  setConfig(config) {
    const requiredEntities = [
      'voltage_l1_entity', 'voltage_l2_entity', 'voltage_l3_entity',
      'voltage_angle_l1_entity', 'voltage_angle_l2_entity', 'voltage_angle_l3_entity',
      'current_l1_entity', 'current_l2_entity', 'current_l3_entity',
      'current_angle_l1_entity', 'current_angle_l2_entity', 'current_angle_l3_entity'
    ];
    for (const entityKey of requiredEntities) {
      if (!config[entityKey]) {
        throw new Error(`Bitte Entität für "${entityKey}" in der Kartenkonfiguration angeben!`);
      }
    }
    this.config = {
        ...config,
        use_german_colors: config.use_german_colors || false, // Standardwert
    };
  }

  static async getConfigElement() {
        // --- BEGINN DES WORKAROUNDS ---
        try {
            if (!customElements.get('ha-entity-picker')) {
                console.warn(
                    "HA-ENTITY-PICKER WORKAROUND: 'ha-entity-picker' ist noch nicht definiert. Versuche, Abhängigkeiten über 'hui-entities-card' zu laden..."
                );
        
                // Versuche, eine Kern-HA-Karte zu "aktivieren", die wahrscheinlich ha-entity-picker verwendet.
                // hui-entities-card ist ein guter Kandidat, da ihr Editor Entity-Picker verwendet.
                const tempElement = document.createElement('hui-entities-card');
        
                // Prüfen, ob die Methode existiert, bevor sie aufgerufen wird
                if (tempElement && typeof tempElement.constructor.getConfigElement === 'function') {
                    // Wir rufen getConfigElement auf, um die Ladevorgänge anzustoßen.
                    // Das Ergebnis selbst benötigen wir hier nicht.
                    await tempElement.constructor.getConfigElement();
                    console.log(
                        "HA-ENTITY-PICKER WORKAROUND: 'hui-entities-card.constructor.getConfigElement()' wurde aufgerufen."
                    );
        
                    if (customElements.get('ha-entity-picker')) {
                        console.log(
                            "HA-ENTITY-PICKER WORKAROUND: ERFOLGREICH! 'ha-entity-picker' ist jetzt definiert."
                        );
                    } else {
                        console.warn(
                            "HA-ENTITY-PICKER WORKAROUND: Teilweise ausgeführt, aber 'ha-entity-picker' ist immer noch nicht definiert."
                        );
                    }
                } else {
                    console.warn(
                        "HA-ENTITY-PICKER WORKAROUND: 'hui-entities-card' oder dessen 'getConfigElement' Methode nicht verfügbar."
                    );
                }
            } else {
                console.log("'ha-entity-picker' ist bereits definiert. Kein Workaround nötig.");
            }
        } catch (err) {
            console.warn("HA-ENTITY-PICKER WORKAROUND: Fehler während des Versuchs:", err);
        }
        // --- ENDE DES WORKAROUNDS ---
      try {
          await import('./fronius-smartmeter-ip-card-editor.js');
          return document.createElement('fronius-smartmeter-ip-card-editor');
      } catch (e) {
          console.error("FroniusCardAdvanced: Kritischer Fehler beim Laden des Editors 'fronius-smartmeter-ip-card-editor.js'.", e);
          const errorDiv = document.createElement('div');
          errorDiv.innerHTML = 'Fehler beim Laden des Karten-Editors. <br>Bitte Browser-Konsole prüfen.';
          return errorDiv;
      }
  }

  static getStubConfig(hass, entities, entitiesFallback) {
    let basePrefix = "sensor.smart_meter_"; // Allgemeinerer Platzhalter
    
    // Versuche, einen Fronius-Präfix zu finden
    const froniusVoltageSensors = Object.keys(hass.states).filter(
      eid => eid.startsWith("sensor.fronius_sm_") && eid.endsWith("_voltage_l1")
    );

    if (froniusVoltageSensors.length > 0) {
      const parts = froniusVoltageSensors[0].split('_');
      if (parts.length > 2) { 
        parts.pop(); // _l1 entfernen
        parts.pop(); // _voltage entfernen
        basePrefix = parts.join('_') + "_"; // z.B. sensor.fronius_sm_geraetename_
      }
    } else {
        // Fallback, falls keine spezifischen Fronius-Sensoren gefunden werden
        const genericSensors = Object.keys(hass.states).filter(
            eid => eid.includes("_voltage_l1") && eid.startsWith("sensor.")
        );
        if (genericSensors.length > 0) {
            const parts = genericSensors[0].split('_');
            if (parts.length > 2) {
                parts.pop();
                parts.pop();
                basePrefix = parts.join('_') + "_"; // z.B. sensor.my_meter_
            }
        }
    }

    // Suffixe basierend auf den ursprünglichen Entitäts-Endungen
    return {
      title: "Smart Meter Phasenplot",
      voltage_l1_entity: `${basePrefix}voltage_l1`,
      voltage_l2_entity: `${basePrefix}voltage_l2`,
      voltage_l3_entity: `${basePrefix}voltage_l3`,
      voltage_angle_l1_entity: `${basePrefix}voltage_phase_angle_l1`,
      voltage_angle_l2_entity: `${basePrefix}voltage_phase_angle_l2`,
      voltage_angle_l3_entity: `${basePrefix}voltage_phase_angle_l3`,
      current_l1_entity: `${basePrefix}current_l1`,
      current_l2_entity: `${basePrefix}current_l2`,
      current_l3_entity: `${basePrefix}current_l3`,
      current_angle_l1_entity: `${basePrefix}current_phase_angle_l1`,
      current_angle_l2_entity: `${basePrefix}current_phase_angle_l2`,
      current_angle_l3_entity: `${basePrefix}current_phase_angle_l3`,
    };
  }

  getCardSize() {
    return 3; 
  }

  render() {
    return html`
          <ha-card header="${this.config.title || 'Phasenplot'}"> <div class="card-content"> <svg id="diagram" viewBox="0 0 340 410" xmlns="http://www.w3.org/2000/svg" xlink="http://www.w3.org/1999/xlink" version="1.1">
                  <marker id="arrowhead0" viewBox="0 0 60 60" refX="60" refY="30" markerUnits="strokeWidth" markerWidth="10" markerHeight="10" orient="auto">
                      <path d="M 0 0 L 60 30 L 0 60 z" fill="#777777"></path>
                  </marker>
                  <marker id="arrowhead1" viewBox="0 0 60 60" refX="0" refY="30" markerUnits="strokeWidth" markerWidth="10" markerHeight="10" orient="auto">
                      <path d="M 0 30 L 60 60 L 60 0 z" fill="#777777"></path>
                  </marker>
                  <marker id="arrowheadA" viewBox="0 0 60 60" refX="60" refY="30" markerUnits="strokeWidth" markerWidth="8" markerHeight="8" orient="auto">
                      <path d="M 0 0 L 60 30 L 0 60 z" fill="#e14621"></path>
                  </marker>
                  <marker id="arrowheadB" viewBox="0 0 60 60" refX="60" refY="30" markerUnits="strokeWidth" markerWidth="8" markerHeight="8" orient="auto">
                      <path d="M 0 0 L 60 30 L 0 60 z" fill="green"></path>
                  </marker>
                  <marker id="arrowheadC" viewBox="0 0 60 60" refX="60" refY="30" markerUnits="strokeWidth" markerWidth="8" markerHeight="8" orient="auto">
                      <path d="M 0 0 L 60 30 L 0 60 z" fill="#1E90FF"></path>
                  </marker>
                  <marker id="arrowheadN" viewBox="0 0 60 60" refX="60" refY="30" markerUnits="strokeWidth" markerWidth="8" markerHeight="8" orient="auto">
                      <path d="M 0 0 L 60 30 L 0 60 z" fill="#000000"></path>
                  </marker>
                  <circle cx="170" cy="170" r="140" style="stroke:#777777;stroke-width:1;" stroke-dasharray="10,0" fill="white"></circle>
                  <line x1="170" y1="0" x2="170" y2="340" style="stroke:#777777;stroke-width:1" stroke-dasharray="5, 5" marker-start="url(#arrowhead1)" marker-end="url(#arrowhead0)"></line>
                  <line x1="0" y1="170" x2="340" y2="170" style="stroke:#777777;stroke-width:1" stroke-dasharray="5, 5" marker-start="url(#arrowhead1)" marker-end="url(#arrowhead0)"></line>
    
                  <text class="voltage" x="325" y="160" text-anchor="end" transform="rotate(90, 325, 160)">+230V</text>
                  <text id="ipr" class="current" x="325" y="180" transform="rotate(90, 325, 180)">+1A</text> 
                  <text class="voltage" x="160" y="15" text-anchor="end">+230iV</text>     
                  <text id="ipi" class="current" x="180" y="15">+1iA</text>
                  <text class="voltage" x="5" y="160" text-anchor="end" transform="rotate(90, 5,160)">-230V</text>
                  <text id="inr" class="current" x="5" y="180" transform="rotate(90, 5,180)">-1A</text>
                  <text class="voltage" x="160" y="335" text-anchor="end">-230iV</text>
                  <text id="ini" class="current" x="180" y="335">-1iA</text>
    
                  <text text-anchor="middle" alignment-baseline="middle" x="235" y="105" class="plottext">Q1</text>
                  <text text-anchor="middle" alignment-baseline="middle" x="105" y="105" class="plottext">Q2</text>
                  <text text-anchor="middle" alignment-baseline="middle" x="105" y="235" class="plottext">Q3</text>
                  <text text-anchor="middle" alignment-baseline="middle" x="235" y="235" class="plottext">Q4</text>
                  <line id="arrowVA" x1="170" y1="170" x2="170" y2="170" class="voltage" marker-end="url(#arrowheadA)"></line>
                  <line id="arrowVB" x1="170" y1="170" x2="170" y2="170" class="voltage" marker-end="url(#arrowheadB)"></line>
                  <line id="arrowVC" x1="170" y1="170" x2="170" y2="170" class="voltage" marker-end="url(#arrowheadC)"></line>
                  <line id="arrowIA" x1="170" y1="170" x2="170" y2="170" class="current" marker-end="url(#arrowheadA)"></line>
                  <line id="arrowIB" x1="170" y1="170" x2="170" y2="170" class="current" marker-end="url(#arrowheadB)"></line>
                  <line id="arrowIC" x1="170" y1="170" x2="170" y2="170" class="current" marker-end="url(#arrowheadC)"></line>
                  <line id="arrowIN" x1="170" y1="170" x2="170" y2="170" class="current" marker-end="url(#arrowheadN)"></line>
                  <svg x="0" y="340">
                      <text class="legend" x="30" y="20">Phase A: Voltage</text>  <line style="stroke-dasharray: 2;" x1="140" y1="20" x2="190" y2="20" class="legend-line phase-a" marker-end="url(#arrowheadA)"></line>
                      <text class="legend" x="200" y="20">Current</text>      <line style="stroke-dasharray: 5;" x1="260" y1="20" x2="310" y2="20" class="legend-line phase-a" marker-end="url(#arrowheadA)"></line>
                      <text class="legend" x="30" y="40">Phase B: Voltage</text>  <line style="stroke-dasharray: 2;" x1="140" y1="40" x2="190" y2="40" class="legend-line phase-b" marker-end="url(#arrowheadB)"></line>
                      <text class="legend" x="200" y="40">Current</text>      <line style="stroke-dasharray: 5;" x1="260" y1="40" x2="310" y2="40" class="legend-line phase-b" marker-end="url(#arrowheadB)"></line>
                      <text class="legend" x="30" y="60">Phase C: Voltage</text>  <line style="stroke-dasharray: 2;" x1="140" y1="60" x2="190" y2="60" class="legend-line phase-c" marker-end="url(#arrowheadC)"></line>
                      <text class="legend" x="200" y="60">Current</text>      <line style="stroke-dasharray: 5;" x1="260" y1="60" x2="310" y2="60" class="legend-line phase-c" marker-end="url(#arrowheadC)"></line>
                  </svg>
              </svg>
            </div>
          </ha-card>
        `;
  }

  firstUpdated(changedProperties) {
    super.firstUpdated(changedProperties);
    this._applyColorTheme(); // Farben initial setzen
    // Der Workaround für den Picker, falls noch vorhanden und benötigt:
    // this._ensurePickerIsDefined();
  }

  updated(changedProperties) { // changedProperties ist der korrekte Parametername
    // Korrekte Abfrage: changedProperties statt changedProps
    if (changedProperties.has('config') || changedProperties.has('hass')) {
        this._applyColorTheme(); // Farben bei Config-Änderung aktualisieren
    }
    // Korrekte Abfrage: changedProperties statt changedProps
    if (changedProperties.has('hass') || changedProperties.has('config')) {
      this._draw();
    }
    // Rufen Sie auch die updated-Methode der Superklasse auf, falls diese Logik enthält (gute Praxis)
    super.updated(changedProperties);
  }

  _draw() {
    if (!this.hass || !this.config) {
      console.warn("FroniusCardAdvanced: hass oder config nicht verfügbar in _draw.");
      return;
    }
    const s = this.hass.states;

    const getValue = (entityIdConfigKey, entityNameForLog) => {
      const entityId = this.config[entityIdConfigKey];
      if (!entityId) {
        // console.warn(`FroniusCardAdvanced: Konfigurationsschlüssel ${entityIdConfigKey} ist nicht gesetzt.`);
        return 0; // Erwartet, dass setConfig Fehler wirft, wenn nicht vorhanden
      }
      if (!s[entityId]) {
        // console.warn(`FroniusCardAdvanced: Entität ${entityId} (${entityNameForLog}) nicht gefunden.`);
        return 0;
      }
      const val = parseFloat(s[entityId]?.state);
      if (isNaN(val)) {
        // console.warn(`FroniusCardAdvanced: Wert für ${entityId} (${entityNameForLog}) ist NaN nach parseFloat. State war: ${s[entityId]?.state}`);
        return 0;
      }
      return val;
    };

    const VA = getValue('voltage_l1_entity', 'Voltage L1');
    const VB = getValue('voltage_l2_entity', 'Voltage L2');
    const VC = getValue('voltage_l3_entity', 'Voltage L3');
    const UAA = getValue('voltage_angle_l1_entity', 'Voltage Angle L1');
    const UAB = getValue('voltage_angle_l2_entity', 'Voltage Angle L2');
    const UAC = getValue('voltage_angle_l3_entity', 'Voltage Angle L3');
    const IA = getValue('current_l1_entity', 'Current L1');
    const IB = getValue('current_l2_entity', 'Current L2');
    const IC = getValue('current_l3_entity', 'Current L3');
    const IAA = getValue('current_angle_l1_entity', 'Current Angle L1');
    const IAB = getValue('current_angle_l2_entity', 'Current Angle L2');
    const IAC = getValue('current_angle_l3_entity', 'Current Angle L3');
    
    this._setCursor('arrowVA', UAA, VA / 230);
    this._setCursor('arrowVB', UAB, VB / 230);
    this._setCursor('arrowVC', UAC, VC / 230);

    function toRadians(degrees) { return degrees * (Math.PI / 180); }
    function toDegrees(radians) { return radians * (180 / Math.PI); }
    
    const absPhaseAngleARad = toRadians(UAA + IAA);
    const absPhaseAngleBRad = toRadians(UAB + IAB);
    const absPhaseAngleCRad = toRadians(UAC + IAC);
    
    const IAx = IA * Math.cos(absPhaseAngleARad);
    const IAy = IA * Math.sin(absPhaseAngleARad);
    const IBx = IB * Math.cos(absPhaseAngleBRad);
    const IBy = IB * Math.sin(absPhaseAngleBRad);
    const ICx = IC * Math.cos(absPhaseAngleCRad);
    const ICy = IC * Math.sin(absPhaseAngleCRad);
    
    const INx = IAx + IBx + ICx;
    const INy = IAy + IBy + ICy;
    
    const IN = Math.sqrt(INx * INx + INy * INy);
    const IAN_rad = Math.atan2(INy, INx);
    const IAN = toDegrees(IAN_rad);
        
    let imax = Math.ceil(Math.max(IA, IB, IC, IN, 0.1));
    if (imax === 0) imax = 1; // Verhindert Division durch Null

    const root = this.shadowRoot;
    if (!root) return; 
    
    const iprEl = root.getElementById('ipr');
    if (iprEl) iprEl.textContent = `+${imax}A`;
    const ipiEl = root.getElementById('ipi');
    if (ipiEl) ipiEl.textContent = `+${imax}iA`;
    const inrEl = root.getElementById('inr');
    if (inrEl) inrEl.textContent = `-${imax}A`;
    const iniEl = root.getElementById('ini');
    if (iniEl) iniEl.textContent = `-${imax}iA`;

    this._setCursor('arrowIA', UAA + IAA, IA / imax);
    this._setCursor('arrowIB', UAB + IAB, IB / imax);
    this._setCursor('arrowIC', UAC + IAC, IC / imax);
    this._setCursor('arrowIN', IAN, IN / imax);
  }

  _setCursor(id, angle, amplitude) {
    if (!this.shadowRoot) return; 
    const xStart = 170;
    const yStart = 170;
    const length = 140;
    const rad = (angle * Math.PI) / 180;

    const numAmplitude = Number(amplitude);
    const safeAmplitude = isNaN(numAmplitude) ? 0 : numAmplitude;

    const x = xStart + length * safeAmplitude * Math.cos(rad);
    const y = yStart - length * safeAmplitude * Math.sin(rad);

    const el = this.shadowRoot.getElementById(id);
    if (el) {
      el.setAttribute('x2', x.toString());
      el.setAttribute('y2', y.toString());
    }
  }
  
  _applyColorTheme() {
    const host = this.shadowRoot.host;
    if (!host) return;

    if (this.config.use_german_colors) {
        host.style.setProperty('--color-l1', 'brown'); // Braun für L1
        host.style.setProperty('--color-l2', 'black'); // Schwarz für L2
        host.style.setProperty('--color-l3', 'grey');  // Grau für L3
        host.style.setProperty('--color-n', 'blue');   // Blau für N
    } else {
        // Standardfarben (aktuelles Schema)
        host.style.setProperty('--color-l1', '#e14621'); // Phase A
        host.style.setProperty('--color-l2', 'green');   // Phase B
        host.style.setProperty('--color-l3', '#1E90FF'); // Phase C
        host.style.setProperty('--color-n', '#000000');  // Neutral
    }
  }
}

customElements.define('fronius-smartmeter-ip-card', FroniusSmartmeterIPCard);