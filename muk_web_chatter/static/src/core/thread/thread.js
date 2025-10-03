import { patch } from "@web/core/utils/patch";

import { Thread } from '@mail/core/common/thread';

/**
 * Patches the Thread component to filter out notification messages based on a prop.
 * This patch extends the Thread component's functionality to allow hiding
 * notification-type messages from the displayed messages list.
 */
patch(Thread.prototype, {
    /**
     * Overrides the displayMessages getter to filter messages.
     * This getter retrieves the messages for the thread and, if the
     * `showNotificationMessages` prop is false, it filters out messages of
     * type 'user_notification' or 'notification'.
     * @returns {Array} The filtered list of messages to be displayed.
     */
    get displayMessages() {
        let messages = (
            this.props.order === 'asc' ?
            this.props.thread.nonEmptyMessages :
            [...this.props.thread.nonEmptyMessages].reverse()
        );
        if (!this.props.showNotificationMessages) {
            messages = messages.filter(
                (msg) => !['user_notification', 'notification'].includes(
                    msg.message_type
                )
            );
        }
        return messages;
    },
});
/**
 * Extends the props of the Thread component to include `showNotificationMessages`.
 * This allows controlling the visibility of notification messages from parent components.
 * @property {boolean} [showNotificationMessages] - Determines if notification messages should be shown.
 */
Thread.props = [
    ...Thread.props,
    'showNotificationMessages?',
];
/**
 * Sets the default value for the `showNotificationMessages` prop to true.
 * By default, all notification messages will be displayed in the thread.
 */
Thread.defaultProps = {
    ...Thread.defaultProps,
    showNotificationMessages: true,
};