import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

import { computeAppsAndMenuItems, reorderApps } from "@web/webclient/menus/menu_helpers";

/**
 * A service that provides access to the application menu and its items.
 * This service allows you to retrieve the current application, get a list of all
 * available application menu items, and select a specific application. It
 * depends on the 'menu' service to perform these actions.
 */
export const appMenuService = {
    dependencies: ["menu"],
    /**
     * Starts the appMenuService and returns an object with methods to interact
     * with the application menu.
     * @param {object} env - The Odoo environment.
     * @param {object} menu - The menu service dependency.
     * @returns {Promise<object>} A promise that resolves to an object with
     * methods for menu interaction.
     */
    async start(env, { menu }) {
        return {
            /**
             * Returns the current application.
             * @returns {object} The current application object.
             */
        	getCurrentApp () {
        		return menu.getCurrentApp();
        	},
            /**
             * Returns a list of all application menu items, optionally reordered
             * based on user settings.
             * @returns {Array} A list of application menu items.
             */
        	getAppsMenuItems() {
				const menuItems = computeAppsAndMenuItems(
					menu.getMenuAsTree('root')
				)
				const apps = menuItems.apps;
				const menuConfig = JSON.parse(
					user.settings?.homemenu_config || 'null'
				);
				if (menuConfig) {
                    reorderApps(apps, menuConfig);
				}
        		return apps;
			},
            /**
			 * Selects a specific application in the menu.
			 * @param {object} app - The application object to select.
			 */
			selectApp(app) {
				menu.selectMenu(app);
			}
        };
    },
};

registry.category("services").add("app_menu", appMenuService);
