/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";
import { QWebPlugin } from '@web_editor/js/backend/QWebPlugin';
let stripHistoryIds;

import { session } from "@web/session";

/**
 * Represents a new class SystrayIcon that extends the functionality of a Component.
 * This class is designed to handle the setup, lazy loading of Wysiwyg,
 * and management of the Wysiwyg editor's properties and behavior.
 * @extends Component
 */
export class SystrayIcon extends Component {
    static components = { Wysiwyg }
    /**
     * Sets up the component's initial state and lifecycle hooks.
     * This function initializes the component's state with an 'open' property,
     * determines the Odoo version (Enterprise or Community),
     * and sets up a hook to lazy load the Wysiwyg editor when the component is about to start.
     */
    setup() {
        this.state = useState({
            open: false,
        })
        this.odoo_version = session.isEnterprise() ? 'Enterprise' : 'Community';
        onWillStart(async() => await this._lazyloadWysiwyg())
    };
    /**
     * Lazily loads the Wysiwyg module and its dependencies if they are not already loaded.
     * This asynchronous function checks for the existence of the Wysiwyg module
     * and its associated plugins. If they are not available, it loads the necessary
     * bundle and retrieves the modules.
     * @returns {Promise<void>} A promise that resolves when the Wysiwyg module and its dependencies are loaded.
     */
    async _lazyloadWysiwyg() {
        let wysiwygModule = await odoo.loader.modules.get('@web_editor/js/wysiwyg/wysiwyg');
        this.MoveNodePlugin = (await odoo.loader.modules.get('@web_editor/js/wysiwyg/MoveNodePlugin'))?.MoveNodePlugin;
        // Otherwise, load the module.
        if (!wysiwygModule) {
            await loadBundle('web_editor.backend_assets_wysiwyg');
            wysiwygModule = await odoo.loader.modules.get('@web_editor/js/wysiwyg/wysiwyg');
            this.MoveNodePlugin = (await odoo.loader.modules.get('@web_editor/js/wysiwyg/MoveNodePlugin')).MoveNodePlugin;
        }
        stripHistoryIds = wysiwygModule.stripHistoryIds;
        this.Wysiwyg = wysiwygModule.Wysiwyg;
    }
    /**
    * Retrieves Wysiwyg properties.
    * This getter returns an object containing the necessary properties for the Wysiwyg editor,
    * including the startWysiwyg function, editingValue, and other options.
    * @returns {object} An object containing Wysiwyg properties.
    */
    get wysiwygProps() {
        return {
            startWysiwyg: this.startWysiwyg.bind(this),
            editingValue: undefined,
            options: this.wysiwygOptions
        }
    }
    /**
     * Returns the Wysiwyg options object.
     * This getter provides a comprehensive set of options for configuring the Wysiwyg editor,
     * including settings for video commands, autostart, collaboration, and more.
     * The 'openPrompt' parameter is included to enable loading the prompt dialog from the Systray.
     * @returns {object} The Wysiwyg options object.
     */
    get wysiwygOptions() {
        return {
            value: "",
            allowCommandVideo: false,
            autostart: false,
            collaborationChannel: undefined,
            editorPlugins: [QWebPlugin, this.MoveNodePlugin],
            field_id: "",
            height: undefined,
            inIframe: false,
            iframeCssAssets: undefined,
            iframeHtmlClass: undefined,
            linkOptions: {
                forceNewWindow: true,
            },
            maxHeight: undefined,
            mediaModalParams: {
                noVideos: true,
                useMediaLibrary: true,
            },
            minHeight: undefined,
            noAttachment: undefined,
            onDblClickEditableMedia: this._onDblClickEditableMedia.bind(this),
            onWysiwygBlur: this._onWysiwygBlur.bind(this),
            placeholder: "",
            resizable: false,
            snippets: undefined,
            tabsize: 0,
            document,
            openPrompt: this.state.open,
            systray: {
                insert: false,
            }
        }
    }
    /**
     * Opens an image in fullscreen mode on double-click.
     * This function is triggered when a user double-clicks on an editable media element.
     * If the element is an image with a valid source, it will be displayed in fullscreen mode.
     * @param {Event} ev - The double-click event object.
     */
    _onDblClickEditableMedia(ev) {
        const el = ev.currentTarget;
        if (el.nodeName === 'IMG' && el.src) {
            this.wysiwyg.showImageFullscreen(el.src);
        }
    }
    /**
     * Handles the blur event for the Wysiwyg editor.
     * This function is called when the Wysiwyg editor loses focus.
     * It avoids saving on blur if the HTML field is in inline mode.
     */
    _onWysiwygBlur() {
        // Avoid save on blur if the html field is in inline mode.
        if (!this.props.isInlineStyle) {
            this.commitChanges();
        }
    }
    /**
     * Initializes and starts the WYSIWYG editor with optional features.
     * This asynchronous function sets up the WYSIWYG editor instance,
     * adds a CSS class to the editable area, and optionally includes a code view button.
     * It also establishes event listeners for editor history and collaborative editing.
     * @param {Object} wysiwyg - The WYSIWYG editor instance to be started.
     */
    async startWysiwyg(wysiwyg) {
        this.wysiwyg = wysiwyg;
        await this.wysiwyg.startEdition();
        wysiwyg.$editable[0].classList.add("odoo-editor-qweb");
        if (this.props.codeview) {
            const $codeviewButtonToolbar = $(`
                <div id="codeview-btn-group" class="btn-group">
                    <button class="o_codeview_btn btn btn-primary">
                        <i class="fa fa-code"></i>
                    </button>
                </div>
            `);
            this.wysiwyg.toolbarEl.append($codeviewButtonToolbar[0]);
            $codeviewButtonToolbar.click(this.toggleCodeView.bind(this));
        }
        this.wysiwyg.odooEditor.addEventListener("historyStep", () =>
            this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this._isDirty())
        );
        if (this.props.isCollaborative) {
            this.wysiwyg.odooEditor.addEventListener("onExternalHistorySteps", () =>
                this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this._isDirty())
            );
        }
        this.isRendered = true;
    }
    /**
     * Handles the click event for the systray icon.
     * This function toggles the 'open' state of the component.
     * When the icon is clicked, it sets the 'open' state to its opposite value,
     * and then resets it to false after a 500ms delay.
     */
    _onClick() {
        this.state.open = !this.state.open
        setTimeout(() => {
            this.state.open = false;
        }, 500);
    };
};
/**
 * Checks if the current Odoo session is an Enterprise version.
 * This function determines the session type by checking for the presence of
 * the 6th element in the `server_version_info` array.
 * @returns {boolean} `true` if the session is Enterprise, `false` otherwise.
 */
session.isEnterprise = function () {
    return !!session.server_version_info[5];
};
SystrayIcon.template = "systray_icon";
export const systrayItem = {
    Component: SystrayIcon,
};
registry.category("systray").add("SystrayIcon", systrayItem);
