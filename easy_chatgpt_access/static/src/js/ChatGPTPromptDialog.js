/** @odoo-module **/
import { ChatGPTPromptDialog } from '@web_editor/js/wysiwyg/widgets/chatgpt_prompt_dialog';
/**
 * Extends the default properties of ChatGPTPromptDialog to include a 'systray' object.
 * The 'systray' object has an 'insert' property set to true, enabling
 * integration with the systray.
 * @property {object} systray - The systray configuration object.
 * @property {boolean} systray.insert - Determines if the dialog should be inserted into the systray.
 */
ChatGPTPromptDialog.defaultProps = {
    ...ChatGPTPromptDialog.defaultProps,
    systray: {
        insert: true,
    }
}
/**
 * Adds an optional `systray` property to the `ChatGPTPromptDialog` component.
 * This property is an object that allows for further customization and integration
 * with the systray.
 * @property {object} systray - The optional systray configuration object.
 */
ChatGPTPromptDialog.props = {
    ...ChatGPTPromptDialog.props,
    systray: { type: Object, optional: true },
}
