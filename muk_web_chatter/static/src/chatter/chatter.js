import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";

import { Chatter } from "@mail/chatter/web_portal/chatter";

/**
 * Patches the Chatter component to add functionality for managing notification
 * messages.
 * This patch extends the Chatter component's setup to initialize the visibility
 * of notification messages from local storage. It also adds a method to toggle
 * the visibility of these messages and persist the setting in local storage.
 */
patch(Chatter.prototype, {
    /**
     * Extends the setup method to initialize the state of notification messages.
     * This function calls the original setup method and then retrieves the
     * visibility state of notification messages from local storage. If the
     * state is not found, it defaults to true (visible).
     */
    setup() {
        super.setup();
        const showNotificationMessages = browser.localStorage.getItem(
            'muk_web_chatter.notifications'
        );
        this.state.showNotificationMessages = (
            showNotificationMessages != null ?
            JSON.parse(showNotificationMessages) : true
        );
    },
    /**
     * Toggles the visibility of notification messages and updates local storage.
     * This function is triggered when the user clicks the notification toggle
     * button. It inverts the current visibility state, updates the component's
     * state, and saves the new state to local storage.
     */
    onClickNotificationsToggle() {
        const showNotificationMessages = !this.state.showNotificationMessages;
        browser.localStorage.setItem(
            'muk_web_chatter.notifications', showNotificationMessages
        );
        this.state.showNotificationMessages = showNotificationMessages;
    },
});


