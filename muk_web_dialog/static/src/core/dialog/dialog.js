import { session } from '@web/session';
import { patch } from '@web/core/utils/patch';

import { Dialog } from '@web/core/dialog/dialog';

/**
 * Patches the Dialog component to add functionality for controlling the dialog size.
 * This patch extends the Dialog component's setup to initialize the dialog's
 * size based on user settings. It also adds a method to toggle the dialog
 * size between fullscreen and its initial size.
 */
patch(Dialog.prototype, {
  /**
   * Extends the setup method to initialize the dialog's size.
   * This function calls the original setup method and then sets the dialog's
   * size based on the user's preference stored in the session. If the user
   * has not chosen to maximize dialogs, the size is taken from the props;
   * otherwise, it is set to fullscreen.
   */
  setup() {
    super.setup();
    this.data.size = (
        session.dialog_size !== 'maximize' ? this.props.size : 'fs'
    );
    this.data.initalSize = this.props?.size || 'lg';
  },
  /**
   * Toggles the dialog size between fullscreen and its initial size.
   * This function is triggered when the user clicks the dialog size toggle
   * button. It checks the current size of the dialog and switches it to the
   * other state (fullscreen or initial size).
   */
  onClickDialogSizeToggle() {
      this.data.size = this.data.size === 'fs' ? this.data.initalSize : 'fs';
  }
});
