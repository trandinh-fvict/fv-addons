import { patch } from '@web/core/utils/patch';
import { useService } from '@web/core/utils/hooks';

import { NavBar } from '@web/webclient/navbar/navbar';
import { AppsMenu } from "@muk_web_theme/webclient/appsmenu/appsmenu";

/**
 * Patches the NavBar component to integrate the custom AppsMenu and its
 * associated service.
 * This patch extends the NavBar's setup to include the `app_menu` service,
 * which is required for the custom AppsMenu to function correctly.
 */
patch(NavBar.prototype, {
    /**
     * Extends the setup method to include the app_menu service.
     * This function calls the original setup method and then initializes the
     * `app_menu` service, making it available within the NavBar component.
     */
	setup() {
        super.setup();
        this.appMenuService = useService('app_menu');
    },
});
/**
 * Patches the NavBar component to replace the default AppsMenu with a custom one.
 * This patch updates the `components` property of the NavBar to use the
 * extended AppsMenu component from the `muk_web_theme` module.
 */
patch(NavBar, {
    components: {
        ...NavBar.components,
        AppsMenu,
    },
});
