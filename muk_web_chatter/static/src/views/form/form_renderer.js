import { useState, useRef } from '@odoo/owl';
import { patch } from '@web/core/utils/patch';
import { browser } from "@web/core/browser/browser";

import { FormRenderer } from '@web/views/form/form_renderer';

/**
 * Patches the FormRenderer to add resizing functionality to the chatter.
 * This patch extends the FormRenderer's setup to initialize the chatter's
 * state, including its width from local storage. It also adds methods to
 * handle the resizing of the chatter via mouse events.
 */
patch(FormRenderer.prototype, {
    /**
     * Extends the setup method to initialize chatter state and references.
     * This function calls the original setup method, then initializes the
     * `chatterState` with the width retrieved from local storage. It also sets
     * up a reference to the chatter container element.
     */
    setup() {
        super.setup();
        this.chatterState = useState({
            width: browser.localStorage.getItem('muk_web_chatter.width'),
        });
        this.chatterContainer = useRef('chatterContainer');
    },
    /**
     * Handles the start of a chatter resize event.
     * This function is triggered on a mousedown event on the resize handle.
     * It sets up 'mousemove' and other event listeners to track the resize
     * process and updates the chatter's width in real-time.
     * @param {MouseEvent} ev - The mousedown event.
     */
    onStartChatterResize(ev) {
        if (ev.button !== 0) {
            return;
        }
        const initialX = ev.pageX;
        const chatterElement = this.chatterContainer.el;
        const initialWidth = chatterElement.offsetWidth;
        const resizeStoppingEvents = [
            'keydown', 'mousedown', 'mouseup'
        ];
        const resizePanel = (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            const newWidth = Math.min(
                Math.max(50, initialWidth - (ev.pageX - initialX)),
                Math.max(chatterElement.parentElement.offsetWidth - 250, 250)
            );
            browser.localStorage.setItem('muk_web_chatter.width', newWidth);
            this.chatterState.width = newWidth;
        };
        const stopResize = (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            if (ev.type === 'mousedown' && ev.button === 0) {
                return;
            }
            document.removeEventListener('mousemove', resizePanel, true);
            resizeStoppingEvents.forEach((stoppingEvent) => {
                document.removeEventListener(stoppingEvent, stopResize, true);
            });
            document.activeElement.blur();
        };
        document.addEventListener('mousemove', resizePanel, true);
        resizeStoppingEvents.forEach((stoppingEvent) => {
            document.addEventListener(stoppingEvent, stopResize, true);
        });
    },
    /**
     * Resets the chatter width on a double-click event.
     * This function removes the stored width from local storage and resets the
     * chatter's width to its default value.
     * @param {MouseEvent} ev - The double-click event.
     */
    onDoubleClickChatterResize(ev) {
    	browser.localStorage.removeItem('muk_web_chatter.width');
        this.chatterState.width = false;
    },
});
