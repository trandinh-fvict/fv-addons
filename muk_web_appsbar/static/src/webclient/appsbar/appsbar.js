import { url } from '@web/core/utils/urls';
import { useService } from '@web/core/utils/hooks';

import { Component, onWillUnmount } from '@odoo/owl';

/**
 * Represents a customizable apps bar component that displays a list of
 * available applications and a company logo.
 * This component listens for application menu changes to re-render itself and
 * provides functionality to switch between applications.
 * @extends Component
 */
export class AppsBar extends Component {
	static template = 'muk_web_appsbar.AppsBar';
    static props = {};
    /**
     * Sets up the component, initializes services, and manages event listeners.
     * This function initializes the company and app_menu services, sets the
     * sidebar image URL if available, and adds an event listener to re-render
     * the component when the application menu changes. It also ensures that the
     * event listener is removed when the component is unmounted.
     */
	setup() {
		this.companyService = useService('company');
        this.appMenuService = useService('app_menu');
    	if (this.companyService.currentCompany.has_appsbar_image) {
            this.sidebarImageUrl = url('/web/image', {
                model: 'res.company',
                field: 'appbar_image',
                id: this.companyService.currentCompany.id,
            });
    	}
    	const renderAfterMenuChange = () => {
            this.render();
        };
        this.env.bus.addEventListener(
        	'MENUS:APP-CHANGED', renderAfterMenuChange
        );
        onWillUnmount(() => {
            this.env.bus.removeEventListener(
            	'MENUS:APP-CHANGED', renderAfterMenuChange
            );
        });
    }
    /**
     * Handles the click event on an application icon.
     * This function calls the `selectApp` method from the app_menu service to
     * switch to the selected application.
     * @param {object} app - The application object that was clicked.
     * @returns {Promise} A promise that resolves when the app is selected.
     */
    _onAppClick(app) {
        return this.appMenuService.selectApp(app);
    }
}
