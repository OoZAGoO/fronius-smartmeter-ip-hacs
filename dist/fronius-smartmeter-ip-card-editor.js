import { LitElement, html, css } from 'https://unpkg.com/lit-element?module';

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

class FroniusSmartmeterIPCardEditor extends LitElement {
    static get properties() {
        return {
            hass: { type: Object },
            _config: { type: Object, state: true },
        };
    }

    setConfig(config) {
        this._config = { ...config };
    }

    _valueChanged(ev) {
        if (!this.hass || !this._config) {
            return;
        }

        const target = ev.target;
        const configKey = target.configValue; // Der von uns gesetzte Schlüssel für die Konfiguration

        if (!configKey) {
            // Falls kein configKey vorhanden ist, ist es vielleicht ein anderes Feld, das wir hier nicht behandeln
            // Beispiel: Der 'title' input könnte stattdessen ein 'name'-Attribut verwenden
            // Für dieses Beispiel gehen wir davon aus, dass alle relevanten Felder 'configValue' haben
             console.warn("Kein 'configValue' auf dem Ziel-Element gefunden:", target);

            // Fallback für Elemente, die 'name' statt 'configValue' verwenden (z.B. Standard-Textfelder)
            if (target.name && this._config[target.name] !== target.value) {
                 this._config = {
                    ...this._config,
                    [target.name]: target.value,
                };
                fireEvent(this, 'config-changed', { config: this._config });
            }
            return;
        }

        let newValue;

        // Spezifische Behandlung für ha-switch
        if (target.tagName === 'HA-SWITCH') {
            newValue = target.checked;
        } else {
            // Fallback für andere Input-Typen (z.B. ha-textfield)
            newValue = target.value;
        }

        // Nur aktualisieren und Event auslösen, wenn sich der Wert tatsächlich geändert hat
        if (this._config[configKey] !== newValue) {
            this._config = {
                ...this._config,
                [configKey]: newValue,
            };
            fireEvent(this, 'config-changed', { config: this._config });
        }
    }
    
    _renderEntityPicker(configKey, label, helperSuffix = "") {
        return html`
            <ha-entity-picker
                label="${label}"
                .hass="${this.hass}"
                .value="${this._config[configKey] || ''}"
                .configValue="${configKey}"
                @value-changed="${this._valueChanged}"
                allow-custom-entity
            ></ha-entity-picker>
            ${helperSuffix ? html`<p class="help-text">Erwarteter Suffix der Entität: <code>${helperSuffix}</code></p>` : ''}
        `;
    }

    render() {
        if (!this.hass || this._config === undefined) {
            return html``;
        }

        // Definiere die Felder für die Entitäten
        const entityFields = [
            { key: 'voltage_l1_entity', label: 'Spannung L1 Entität', suffix: '_voltage_l1' },
            { key: 'voltage_l2_entity', label: 'Spannung L2 Entität', suffix: '_voltage_l2' },
            { key: 'voltage_l3_entity', label: 'Spannung L3 Entität', suffix: '_voltage_l3' },
            { key: 'voltage_angle_l1_entity', label: 'Spannungswinkel L1 Entität', suffix: '_voltage_phase_angle_l1' },
            { key: 'voltage_angle_l2_entity', label: 'Spannungswinkel L2 Entität', suffix: '_voltage_phase_angle_l2' },
            { key: 'voltage_angle_l3_entity', label: 'Spannungswinkel L3 Entität', suffix: '_voltage_phase_angle_l3' },
            { key: 'current_l1_entity', label: 'Strom L1 Entität', suffix: '_current_l1' },
            { key: 'current_l2_entity', label: 'Strom L2 Entität', suffix: '_current_l2' },
            { key: 'current_l3_entity', label: 'Strom L3 Entität', suffix: '_current_l3' },
            { key: 'current_angle_l1_entity', label: 'Stromwinkel L1 Entität (rel. zu V L1)', suffix: '_current_phase_angle_l1' },
            { key: 'current_angle_l2_entity', label: 'Stromwinkel L2 Entität (rel. zu V L2)', suffix: '_current_phase_angle_l2' },
            { key: 'current_angle_l3_entity', label: 'Stromwinkel L3 Entität (rel. zu V L3)', suffix: '_current_phase_angle_l3' }
        ];

        return html`
            <div class="card-config">
                <ha-textfield
                    label="Titel (Optional)"
                    .value="${this._config.title || ''}"
                    .configValue="${"title"}"
                    @input="${this._valueChanged}" 
                ></ha-textfield>
                <ha-formfield label="Deutsche Phasenfarben verwenden (L1: Braun, L2: Schwarz, L3: Grau, N: Blau)">
                    <ha-switch
                        .checked="${this._config.use_german_colors || false}"
                        .configValue="${"use_german_colors"}"
                        @change="${this._valueChanged}"
                    ></ha-switch>
                </ha-formfield>
                ${entityFields.map(field => 
                    this._renderEntityPicker(
                        field.key, 
                        field.label,
                        field.suffix // Übergabe des Suffix als Hilfetext
                    )
                )}
                
                <p class="help-text" style="margin-top: 16px;">
                    Stelle hier die Entitäten für jede benötigte Messgröße ein. 
                    Die Karte erwartet numerische Werte von diesen Sensoren.
                    Die Stromphasenwinkel (z.B. für L1) sollten relativ zum jeweiligen Spannungswinkel (z.B. von L1) sein.
                </p>
            </div>
        `;
    }

    static get styles() {
        return css`
            .card-config ha-textfield,
            .card-config ha-entity-picker {
                display: block;
                margin-bottom: 8px;
            }
            .help-text {
                font-size: 0.9em;
                color: var(--secondary-text-color);
                padding-top: 0px;
                padding-bottom: 8px;
                margin-top: -4px; /* Closer to the picker */
            }
            .help-text code {
                background-color: var(--code-background-color, #f0f0f0);
                padding: 0.1em 0.3em;
                border-radius: 3px;
            }
        `;
    }
}

customElements.define('fronius-smartmeter-ip-card-editor', FroniusSmartmeterIPCardEditor);

//document.createElement('hui-media-control-card').constructor.getConfigElement();
window.customCards = window.customCards || [];
window.customCards.push({
  type: "fronius-smartmeter-ip-card", 
  name: "Fronius Smartmeter IP Phasenplot Karte (Konfigurierbare Entitäten)", 
  preview: true,
  description: "Eine Karte zur Visualisierung von Smart Meter Phasenvektoren mit individuell konfigurierbaren Entitäten." 
});