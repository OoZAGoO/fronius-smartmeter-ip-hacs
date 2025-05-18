// fronius-smartmeter-ip-card-simple-editor.js
import { LitElement, html, css } from 'https://unpkg.com/lit-element?module';

// Hilfsfunktion zum Auslösen von Events (Standard in vielen Lovelace-Karten)
const fireEvent = (node, type, detail = {}, options = {}) => {
    const event = new Event(type, {
        bubbles: options.bubbles === undefined ? true : options.bubbles,
        cancelable: Boolean(options.cancelable),
        composed: options.composed === undefined ? true : options.composed,
    });
    event.detail = detail;
    node.dispatchEvent(event);
    return event;
};

class FroniusSmartmeterIPCardSimpleEditor extends LitElement {
    static get properties() {
        return {
            hass: { type: Object },
            _config: { type: Object, state: true }, // Interne Kopie der Konfiguration
        };
    }

    setConfig(config) {
        // Speichere eine Kopie der Konfiguration, um sie im Editor zu bearbeiten
        this._config = { ...config };
    }

    _valueChanged(ev) {
        if (!this.hass || !this._config) {
            return;
        }

        const target = ev.target;
        let value = target.value;

        if (target.type === 'checkbox') {
            value = target.checked;
        }

        const newConfig = {
            ...this._config,
            [target.configValue]: value === "" && target.type !== 'checkbox' ? undefined : value,
        };
        
        fireEvent(this, "config-changed", { config: newConfig });
    }

    render() {
        if (!this.hass || this._config === undefined) {
            return html``;
        }

        return html`
            <div class="card-config">
                <ha-textfield
                    label="Titel (Optional)"
                    .value="${this._config.title || ''}"
                    .configValue="${"title"}"
                    @input="${this._valueChanged}"
                ></ha-textfield>

                <ha-textfield
                    label="Entitäten-Präfix"
                    helper="z.B. sensor.fronius_sm_DIE_GERAETE_IP"
                    .value="${this._config.entity_prefix || ''}"
                    .configValue="${"entity_prefix"}"
                    @input="${this._valueChanged}"
                    required
                    auto-validate
                    pattern="^sensor\.[\w_]+$" 
                    error-message="Ungültiger Präfix! Muss mit 'sensor.' beginnen."
                ></ha-textfield>
                <p class="help-text">
                    Der Präfix ist der gemeinsame Teil deiner Fronius Sensor-Entitäts-IDs,
                    bis zum spezifischen Messteil (z.B. '_voltage_l1').<br>
                    Beispiel: Wenn dein Sensor <code>sensor.fronius_sm_192_168_2_21_voltage_l1</code> heißt,
                    ist der Präfix <code>sensor.fronius_sm_192_168_2_21</code>.
                </p>
            </div>
        `;
    }

    static get styles() {
        return css`
            .card-config ha-textfield {
                display: block;
                margin-bottom: 16px;
            }
            .help-text {
                font-size: 0.9em;
                color: var(--secondary-text-color);
                padding-top: 4px;
                padding-bottom: 8px;
            }
        `;
    }
}

customElements.define('fronius-smartmeter-ip-card-simple-editor', FroniusSmartmeterIPCardSimpleEditor);
// Optional: Setze die window-Variable, damit der Lovelace UI-Editor die Karte findet,
// falls der dynamische Import in der Hauptkarte nicht perfekt funktioniert oder für ältere HA-Versionen.
window.customCards = window.customCards || [];
window.customCards.push({
  type: "fronius-smartmeter-ip-card-simple",
  name: "Fronius Smartmeter IP Phasenplot Karte",
  preview: true, // Optional: true, wenn eine Vorschau im Editor möglich ist
  description: "Eine Karte zur Visualisierung von Fronius Smart Meter IP Phasenvektoren." // Optional
});
