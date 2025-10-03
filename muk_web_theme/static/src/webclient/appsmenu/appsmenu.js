import { useEffect } from "@odoo/owl";
import { url } from "@web/core/utils/urls";
import { useBus, useService } from "@web/core/utils/hooks";

import { Dropdown } from "@web/core/dropdown/dropdown";

/**
 * Represents the main applications menu, extending the Dropdown component.
 * This class manages the display of the apps menu, including a custom
 * background image and a keyboard shortcut to open the command palette.
 * @extends Dropdown
 */
export class AppsMenu extends Dropdown {
    /**
     * Sets up the component, initializes services, and manages event listeners.
     * This function initializes the command and company services, sets the
     * background image URL, and adds a keydown event listener to open the
     * command palette when the menu is open. It also ensures that the menu
     * closes when the UI is updated.
     */
    setup() {
    	super.setup();
    	this.commandPaletteOpen = false;
        this.commandService = useService("command");
    	this.companyService = useService('company');
    	if (this.companyService.currentCompany.has_background_image) {
            this.imageUrl = url('/web/image', {
                model: 'res.company',
                field: 'background_image',
                id: this.companyService.currentCompany.id,
            });
    	} else {
    		this.imageUrl = '/muk_web_theme/static/src/img/background.png';
    	}
        useEffect(
            (isOpen) => {
            	if (isOpen) {
            		const openMainPalette = (ev) => {
            	    	if (
            	    		!this.commandServiceOpen && 
            	    		ev.key.length === 1 &&
            	    		!ev.ctrlKey &&
            	    		!ev.altKey
            	    	) {
	            	        this.commandService.openMainPalette(
            	        		{ searchValue: `/${ev.key}` }, 
            	        		() => { this.commandPaletteOpen = false; }
            	        	);
	            	    	this.commandPaletteOpen = true;
            	    	}
            		}
	            	window.addEventListener("keydown", openMainPalette);
	                return () => {
	                	window.removeEventListener("keydown", openMainPalette);
	                	this.commandPaletteOpen = false;
	                }
            	}
            },
            () => [this.state.isOpen]
		);
    	useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", this.state.close);
    }
    /**
     * Sets the background image of the menu when it is opened.
     * This function is called after the dropdown menu is opened, and it sets
     * the background image of the menu element to the URL determined in the
     * setup method.
     */
    onOpened() {
		super.onOpened();
		if (this.menuRef && this.menuRef.el) {
			this.menuRef.el.style.backgroundImage = `url('${this.imageUrl}')`;
		}
    }
}
