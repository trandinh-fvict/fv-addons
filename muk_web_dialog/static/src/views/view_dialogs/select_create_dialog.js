import { patch } from '@web/core/utils/patch';

import { SelectCreateDialog } from '@web/views/view_dialogs/select_create_dialog';

/**
 * Patches the SelectCreateDialog component to add functionality for toggling the dialog size.
 * This patch adds a method to toggle the dialog size between fullscreen and its
 * initial size, using the dialogData from the environment.
 */
patch(SelectCreateDialog.prototype, {
    /**
     * Toggles the dialog size between fullscreen and its initial size.
     * This function is triggered when the user clicks the dialog size toggle
     * button. It checks the current size of the dialog in the environment's
     * dialogData and switches it to the other state (fullscreen or initial size).
     */
    onClickDialogSizeToggle() {
        this.env.dialogData.size = (
            this.env.dialogData.size === 'fs' ? this.env.dialogData.initalSize : 'fs'
        );
    }
});