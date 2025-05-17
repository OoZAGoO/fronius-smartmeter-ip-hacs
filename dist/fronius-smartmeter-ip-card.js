import { LitElement, html, css } from 'https://unpkg.com/lit-element?module';

class FroniusSmartmeterIPCard extends LitElement {
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
    if (!config.entities 
        || !config.entities.voltage_l1 || !config.entities.voltage_l2 || !config.entities.voltage_l3 
        || !config.entities.voltage_angle_l1 || !config.entities.voltage_angle_l2 || !config.entities.voltage_angle_l3 
        || !config.entities.current_l1 || !config.entities.current_l2 || !config.entities.current_l3 
        || !config.entities.current_angle_l1 || !config.entities.current_angle_l2 || !config.entities.current_angle_l3 
      ) {
        throw new Error('Bitte alle benötigten Entitäten in der Kartenkonfiguration angeben!');
    }
    this.config = config; // Speichere die gesamte Konfiguration
}

  static async getConfigElement() {
    // Hier könntest du ein UI für die Konfiguration deiner Karte erstellen, wenn du möchtest
    // Für den Anfang nicht notwendig.
    // await import("./fronius-smartmeter-ip-card-editor"); // Beispiel für eine separate Editor-Datei
    // return document.createElement("fronius-smartmeter-ip-card-editor");
    return null; // Kein visueller Editor für den Anfang
  }

  static getStubConfig(hass, entities, entitiesFallback) {
      // Diese Funktion wird aufgerufen, wenn der Benutzer die Karte zum ersten Mal hinzufügt.
      // Sie kann eine Standardkonfiguration vorschlagen.
      // Du musst hier die Entitäts-IDs finden, die zu deinem Schema passen könnten.
      // Das ist fortgeschrittener, für den Anfang kannst du eine Basis-Stub-Config zurückgeben.
      const L1VoltageSensors = entities.filter(eid => eid.endsWith("_voltage_l1") && eid.includes("fronius_sm"));
      // ... ähnliche Logik für andere Sensoren
      return { 
          title: "Fronius Phase Plot",
          entities: {
              voltage_l1: L1VoltageSensors.length > 0 ? L1VoltageSensors[0] : "sensor.example_voltage_l1",
              // Fülle weitere Entitäten basierend auf Logik oder als Platzhalter
          }
      };
  }

  getCardSize() {
      return 5; // Schätze, wie viele Standard-Zeilen deine Karte ungefähr belegt (z.B. 5 für deine SVG-Höhe)
  }

    render() {
        return html`
          <ha-card header="${this.config.title}"> <div class="card-content"> <svg id="diagram" viewBox="0 0 340 440" xmlns="http://www.w3.org/2000/svg" xlink="http://www.w3.org/1999/xlink" version="1.1">
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
    if (!this.hass || !this.config.entities) {
      return;
    }
    // Lesen der Sensorwerte aus HA
    const s = this.hass.states;
    const entities = this.config.entities;

    console.log("Voltage:", entities.voltage_l1);
    console.log("Voltage:", s[entities.voltage_l1]?.state);

    const VA = parseFloat(s[entities.voltage_l1]?.state) || 0;
    const VB = parseFloat(s[entities.voltage_l2]?.state) || 0;
    const VC = parseFloat(s[entities.voltage_l3]?.state) || 0;
    const UAA = parseFloat(s[entities.voltage_angle_l1]?.state) || 0;
    const UAB = parseFloat(s[entities.voltage_angle_l2]?.state) || 0;
    const UAC = parseFloat(s[entities.voltage_angle_l3]?.state) || 0;
    const IA = parseFloat(s[entities.current_l1]?.state) || 0;
    const IB = parseFloat(s[entities.current_l2]?.state) || 0;
    const IC = parseFloat(s[entities.current_l3]?.state) || 0;
    const IAA = parseFloat(s[entities.current_angle_l1]?.state) || 0;
    const IAB = parseFloat(s[entities.current_angle_l2]?.state) || 0;
    const IAC = parseFloat(s[entities.current_angle_l3]?.state) || 0;

    console.log("VA:", VA, "UAA:", UAA, "IA:", IA, "IAA:", IAA);
    console.log("VB:", VB, "UAB:", UAB, "IB:", IB, "IAB:", IAB);
    console.log("VC:", VC, "UAC:", UAC, "IC:", IC, "IAC:", IAC);

    // Erstes Set: Spannungspfeile
    this._setCursor('arrowVA', UAA, VA / 230);
    this._setCursor('arrowVB', UAB, VB / 230);
    this._setCursor('arrowVC', UAC, VC / 230);

    // Strom-Maximum berechnen
    let imax = Math.ceil(Math.max(IA, IB, IC, 0.1));
    console.log("imax:", imax);

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

customElements.define('fronius-smartmeter-ip-card', FroniusSmartmeterIPCard);
