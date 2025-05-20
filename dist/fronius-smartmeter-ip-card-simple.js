import { LitElement, html, css } from 'https://unpkg.com/lit-element?module';

class FroniusSmartmeterIPCardSimple extends LitElement {
  static get type() {
    return 'fronius-smartmeter-ip-card-simple'; // Muss mit dem Tag in customElements.define() übereinstimmen
  }

  static get name() {
    return 'Fronius Smartmeter Phasenplot'; // Ein benutzerfreundlicher Name für den Auswahl-Dialog
  }

  static get description() {
    // Eine Beschreibung hinzufügen, kann manchmal helfen.
    return 'Visualisiert Spannungs- und Stromphasenvektoren für den Fronius Smart Meter IP.';
  }

  static get preview() {
    // Explizit angeben, ob eine Vorschau versucht werden soll.
    // true: HA versucht, eine Vorschau basierend auf getStubConfig zu rendern.
    // false: Es wird keine Vorschau versucht (Karte könnte trotzdem gelistet werden).
    // Teste beide Werte (true und false), beginne mit true.
    return true;
  }

  // Diese Methode signalisiert, dass deine Karte den Lovelace UI-Editor unterstützt.
  // Sie ist besonders wichtig, wenn du getConfigElement und getStubConfig verwendest.
  static getLovelaceConfig() {
    return {
      type: this.type, // Verweist auf static get type()
      // Hier könntest du auch Standardwerte für die Stub-Konfiguration angeben,
      // aber getStubConfig ist dafür der primäre Ort.
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
          }
          ha-card {
            overflow: hidden; /* Wichtig, um den Inhalt zu begrenzen */
          }
          .card-content { /* Neuer Wrapper für das SVG */
            padding: 16px;
            display: flex;
            justify-content: center; /* Zentriert das SVG horizontal */
            align-items: center;
          }
          svg#diagram { /* Nur das Haupt-SVG ansprechen */
            width: 100%;
            max-width: 340px; /* Behält die Originalbreite als Maximum bei */
            height: auto;    /* Höhe passt sich an, um Seitenverhältnis via viewBox zu wahren */
            /* font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; /* Aus body übernommen */
          }
    
          /* Relevante Stile aus der originalen CSS, angepasst */
          .plottext {
            font-size: 12pt; /* Evtl. px oder em für bessere Skalierbarkeit in HA verwenden */
            fill: #777777;
          }
          .legend {
            font-size: 10pt; /* Evtl. px oder em */
            fill: var(--secondary-text-color);
            /* alignment-baseline ist ein SVG-Attribut, nicht CSS. Kann direkt am <text>-Element gesetzt werden. */
          }
          text.voltage {
            fill: #e14621;
          }
          text.current {
            fill: #1E90FF;
          }
          line.voltage {
            stroke: #e14621;
            stroke-width: 1.5; /* Etwas dicker für bessere Sichtbarkeit, original war 1 */
            stroke-dasharray: 2; /* Testweise auskommentieren, um zu sehen, ob durchgezogene Linien erscheinen */
          }
          line.current {
            stroke: #1E90FF;
            stroke-width: 1.5; /* Etwas dicker für bessere Sichtbarkeit, original war 1 */
            stroke-dasharray: 5; /* Testweise auskommentieren */
          }
        `;
  }

  setConfig(config) {
    if (!config.entity_prefix) {
      throw new Error('Bitte "entity_prefix" in der Kartenkonfiguration angeben!');
    }
    this.config = config; // Speichere die gesamte Konfiguration
  }

  static async getConfigElement() {
      // console.log("FroniusCard: getConfigElement wird aufgerufen"); // Debug-Log
      try {
          // Sicherstellen, dass der Pfad zur Editor-Datei exakt stimmt (Groß-/Kleinschreibung!)
          // und dass die Editor-Datei selbst keine Syntaxfehler hat.
          await import('./fronius-smartmeter-ip-card-simple-editor.js');
          return document.createElement('fronius-smartmeter-ip-card-simple-editor');
      } catch (e) {
          console.error("FroniusCard: Kritischer Fehler beim Laden des Editors 'fronius-smartmeter-ip-card-simple-editor.js'. Dies könnte die Anzeige im Picker verhindern.", e);
          // Im Fehlerfall ein einfaches Element zurückgeben, um den Prozess nicht komplett abzubrechen.
          const errorDiv = document.createElement('div');
          errorDiv.innerHTML = 'Fehler beim Laden des Karten-Editors. <br>Bitte Browser-Konsole prüfen.';
          return errorDiv;
      }
  }

  static getStubConfig(hass, entities, entitiesFallback) {
    // Diese Funktion wird aufgerufen, wenn der Benutzer die Karte zum ersten Mal hinzufügt.
    // Sie kann eine Standardkonfiguration vorschlagen.
    let suggestedPrefix = "sensor.fronius_sm_meine_geraete_id"; // Standard-Platzhalter

    // Versuche, einen passenden Präfix aus vorhandenen Entitäten zu finden
    // Sucht nach einem Sensor, der typischerweise von dieser Integration erstellt wird (z.B. _voltage_l1)
    const froniusVoltageSensors = Object.keys(hass.states).filter(
      eid => eid.startsWith("sensor.fronius_sm_") && eid.endsWith("_voltage_l1")
    );

    if (froniusVoltageSensors.length > 0) {
      // Extrahiere den Präfix: sensor.fronius_sm_geraetename_voltage_l1 -> sensor.fronius_sm_geraetename
      const parts = froniusVoltageSensors[0].split('_');
      if (parts.length > 2) { // Stellt sicher, dass genug Teile vorhanden sind
        parts.pop(); // Entfernt '_l1'
        parts.pop(); // Entfernt '_voltage'
        suggestedPrefix = parts.join('_');
      }
    }

    return {
      title: "Fronius Phasenplot",
      entity_prefix: suggestedPrefix
    };
  }

  getCardSize() {
    return 3; // Schätze, wie viele Standard-Zeilen deine Karte ungefähr belegt (z.B. 5 für deine SVG-Höhe)
  }

  render() {
    return html`
          <ha-card header="${this.config.title}"> <div class="card-content"> <svg id="diagram" viewBox="0 0 340 410" xmlns="http://www.w3.org/2000/svg" xlink="http://www.w3.org/1999/xlink" version="1.1">
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
                  <svg x="0" y="340"> <text class="legend" x="30" y="20">Phase A: Voltage</text>  <line x1="140" y1="20" x2="190" y2="20" class="voltage" marker-end="url(#arrowheadA)"></line>
                      <text class="legend" x="200" y="20">Current</text>      <line x1="260" y1="20" x2="310" y2="20" class="current" marker-end="url(#arrowheadA)"></line>
                      <text class="legend" x="30" y="40">Phase B: Voltage</text>  <line x1="140" y1="40" x2="190" y2="40" class="voltage" marker-end="url(#arrowheadB)"></line>
                      <text class="legend" x="200" y="40">Current</text>      <line x1="260" y1="40" x2="310" y2="40" class="current" marker-end="url(#arrowheadB)"></line>
                      <text class="legend" x="30" y="60">Phase C: Voltage</text>  <line x1="140" y1="60" x2="190" y2="60" class="voltage" marker-end="url(#arrowheadC)"></line> 
                      <text class="legend" x="200" y="60">Current</text>      <line x1="260" y1="60" x2="310" y2="60" class="current" marker-end="url(#arrowheadC)"></line>   
                  </svg>
              </svg>
            </div>
          </ha-card>
        `;
  }

  updated(changedProps) {
    if (changedProps.has('hass')) {
      this._draw();
    }
  }

  _draw() {
    if (!this.hass || !this.config || !this.config.entity_prefix) {
      console.warn("FroniusCard: hass oder entity_prefix nicht verfügbar in _draw.");
      return;
    }
    const s = this.hass.states;
    const prefix = this.config.entity_prefix;

    const getValue = (suffix, entityNameForLog) => {
      const entityId = `${prefix}${suffix}`;
      if (!s[entityId]) {
        console.warn(`FroniusCard: Entität ${entityId} (${entityNameForLog}) nicht gefunden.`);
        return 0;
      }
      const val = parseFloat(s[entityId]?.state) || 0;
      if (isNaN(val)) {
        console.warn(`FroniusCard: Wert für ${entityId} (${entityNameForLog}) ist NaN nach parseFloat.`);
        return 0;
      }
      return val;
    };

    // Suffixe basierend auf den Entitäts-ID-Endungen (kleingeschrieben, von SensorEntityDescription.name abgeleitet)
    const VA = getValue('_voltage_l1', 'Voltage L1');
    const VB = getValue('_voltage_l2', 'Voltage L2');
    const VC = getValue('_voltage_l3', 'Voltage L3');
    const UAA = getValue('_voltage_phase_angle_l1', 'Voltage Angle L1');
    const UAB = getValue('_voltage_phase_angle_l2', 'Voltage Angle L2');
    const UAC = getValue('_voltage_phase_angle_l3', 'Voltage Angle L3');
    const IA = getValue('_current_l1', 'Current L1');
    const IB = getValue('_current_l2', 'Current L2');
    const IC = getValue('_current_l3', 'Current L3');
    const IAA = getValue('_current_phase_angle_l1', 'Current Phase Angle L1');
    const IAB = getValue('_current_phase_angle_l2', 'Current Phase Angle L2');
    const IAC = getValue('_current_phase_angle_l3', 'Current Phase Angle L3');

    // Erstes Set: Spannungspfeile
    this._setCursor('arrowVA', UAA, VA / 230);
    this._setCursor('arrowVB', UAB, VB / 230);
    this._setCursor('arrowVC', UAC, VC / 230);

    // Berechnung des Stroms im Neutralleiter
    // Hilfsfunktion: Grad in Radiant umrechnen
    function toRadians(degrees) {
        return degrees * (Math.PI / 180);
    }
    
    // Hilfsfunktion: Radiant in Grad umrechnen
    function toDegrees(radians) {
        return radians * (180 / Math.PI);
    }
    
    // 1. Absolute Phasenwinkel der Ströme berechnen (in Radiant für die Math-Funktionen)
    // Der gegebene Stromphasenwinkel (IAA, IAB, IAC) ist relativ zum jeweiligen Spannungsphasenwinkel (UAA, UAB, UAC).
    const absPhaseAngleARad = toRadians(UAA + IAA);
    const absPhaseAngleBRad = toRadians(UAB + IAB);
    const absPhaseAngleCRad = toRadians(UAC + IAC);
    
    // 2. Ströme in kartesische Komponenten (Real- und Imaginärteil) umwandeln
    // I_real = I_betrag * cos(winkel_rad)
    // I_imag = I_betrag * sin(winkel_rad)
    
    const IAx = IA * Math.cos(absPhaseAngleARad);
    const IAy = IA * Math.sin(absPhaseAngleARad);
    
    const IBx = IB * Math.cos(absPhaseAngleBRad);
    const IBy = IB * Math.sin(absPhaseAngleBRad);
    
    const ICx = IC * Math.cos(absPhaseAngleCRad);
    const ICy = IC * Math.sin(absPhaseAngleCRad);
    
    // 3. Komponenten der Phasenströme addieren, um die Komponenten des Neutralleiterstroms zu erhalten
    const INx = IAx + IBx + ICx;
    const INy = IAy + IBy + ICy;
    
    // 4. Neutralleiterstrom von kartesischen Komponenten zurück in Polarform (Betrag und Winkel) umwandeln
    const IN = Math.sqrt(INx * INx + INy * INy); // Betrag des Neutralleiterstroms
    
    // Winkel des Neutralleiterstroms in Radiant berechnen
    // Math.atan2(y, x) gibt den Winkel in Radiant zwischen der positiven x-Achse und dem Punkt (x, y) zurück.
    const IAN_rad = Math.atan2(INy, INx);
    
    // Winkel in Grad umwandeln
    const IAN = toDegrees(IAN_rad);
    
    // Ausgabe der Ergebnisse (kann an Ihre Bedürfnisse angepasst werden)
    console.log("Strom im Neutralleiter (IN): " + IN.toFixed(3) + " A");
    console.log("Phasenwinkel des Neutralleiterstroms (IAN): " + IAN.toFixed(3) + " Grad");
    
    // Strom-Maximum berechnen
    let imax = Math.ceil(Math.max(IA, IB, IC, IN, 0.1));

    // Skalierungstexte aktualisieren
    const root = this.shadowRoot;
    root.getElementById('ipr').textContent = `+${imax}A`;
    root.getElementById('ipi').textContent = `+${imax}iA`;
    root.getElementById('inr').textContent = `-${imax}A`;
    root.getElementById('ini').textContent = `-${imax}iA`;

    // Zweites Set: Strompfeile
    this._setCursor('arrowIA', UAA + IAA, IA / imax);
    this._setCursor('arrowIB', UAB + IAB, IB / imax);
    this._setCursor('arrowIC', UAC + IAC, IC / imax);
    
    // Zusatz: Neturalleiter plotten
    this._setCursor('arrowIN', IAN, IN / imax);


  }

  _setCursor(id, angle, amplitude) {
    const xStart = 170;
    const yStart = 170;
    const length = 140;
    const rad = (angle * Math.PI) / 180;
    const x = xStart + length * amplitude * Math.cos(rad);
    const y = yStart - length * amplitude * Math.sin(rad);

    const el = this.shadowRoot.getElementById(id);
    if (el) {
      el.setAttribute('x2', x);
      el.setAttribute('y2', y);
    }
  }
}

customElements.define('fronius-smartmeter-ip-card-simple', FroniusSmartmeterIPCardSimple);
