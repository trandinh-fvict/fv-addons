import { session } from '@web/session';
import { patch } from '@web/core/utils/patch';
import { append, createElement, setAttributes } from '@web/core/utils/xml';

import {FormCompiler} from '@web/views/form/form_compiler';

/**
 * Patches the FormCompiler to modify the form view's XML structure based on the
 * chatter position setting.
 * This patch extends the `compile` method to adjust the chatter's placement
 * and behavior. If the chatter is positioned at the bottom, it moves the
 * chatter component within the form sheet. If it's positioned on the side, it
 * adds a resize handle.
 */
patch(FormCompiler.prototype, {
    /**
     * Extends the compile method to modify the form's XML for chatter placement.
     * This function first calls the original compile method, then inspects the
     * resulting XML. Based on the `chatter_position` in the session, it either
     * moves the chatter to the bottom of the form or adds a resize handle for
     * the side chatter.
     * @param {Element} node - The XML element to compile.
     * @param {object} params - The compilation parameters.
     * @returns {Element} The modified XML element.
     */
    compile(node, params) {
        const res = super.compile(node, params);
        const chatterContainerHookXml = res.querySelector(
            '.o_form_renderer > .o-mail-Form-chatter'
        );
        if (!chatterContainerHookXml) {
            return res;
        }
        setAttributes(chatterContainerHookXml, {
            't-ref': 'chatterContainer',
        });
        if (session.chatter_position === 'bottom') {
            const formSheetBgXml = res.querySelector('.o_form_sheet_bg');
            if (!chatterContainerHookXml || !formSheetBgXml?.parentNode) {
            	return res;
            }
            const webClientViewAttachmentViewHookXml = res.querySelector(
            	'.o_attachment_preview'
            );
            const chatterContainerXml = chatterContainerHookXml.querySelector(
                "t[t-component='__comp__.mailComponents.Chatter']"
            );
            const sheetBgChatterContainerHookXml = chatterContainerHookXml.cloneNode(true);
            const sheetBgChatterContainerXml = sheetBgChatterContainerHookXml.querySelector(
                "t[t-component='__comp__.mailComponents.Chatter']"
            );
            sheetBgChatterContainerHookXml.classList.add('o-isInFormSheetBg', 'w-auto');
            append(formSheetBgXml, sheetBgChatterContainerHookXml);
            setAttributes(sheetBgChatterContainerXml, {
                isInFormSheetBg: 'true',
                isChatterAside: 'false',
            });
            setAttributes(chatterContainerXml, {
                isInFormSheetBg: 'true',
                isChatterAside: 'false',
            });
            setAttributes(chatterContainerHookXml, {
                't-if': 'false',
            });
            if (webClientViewAttachmentViewHookXml) {
                setAttributes(webClientViewAttachmentViewHookXml, {
                    't-if': 'false',
                });
            }
        } else {
            setAttributes(chatterContainerHookXml, {
                't-att-style': '__comp__.chatterState.width ? `width: ${__comp__.chatterState.width}px;` : ""',
            });
            const chatterContainerResizeHookXml = createElement('span');
            chatterContainerResizeHookXml.classList.add('mk_chatter_resize');
            setAttributes(chatterContainerResizeHookXml, {
                't-on-mousedown.stop.prevent': '__comp__.onStartChatterResize.bind(__comp__)',
                't-on-dblclick.stop.prevent': '__comp__.onDoubleClickChatterResize.bind(__comp__)',
            });
            append(chatterContainerHookXml, chatterContainerResizeHookXml);
        }
        return res;
    },
});
