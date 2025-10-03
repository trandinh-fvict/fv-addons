from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    @property
    def THEME_COLOR_FIELDS(self):
        """
        Returns a list of the theme color fields that can be customized.
        These fields correspond to the different color variables used in the
        application's theme, such as the text color for the apps menu and the
        background color for the app bar.
        Returns:
            list: A list of theme color field names.
        """
        return [
            'color_appsmenu_text',
            'color_appbar_text',
            'color_appbar_active',
            'color_appbar_background',
        ]

    @property
    def COLOR_ASSET_THEME_URL(self):
        """
        Returns the URL of the SCSS file for the theme's custom colors.
        This file contains the color variables that will be modified when
        customizing the theme.
        Returns:
            str: The URL of the theme's SCSS file.
        """
        return '/muk_web_theme/static/src/scss/colors.scss'
        
    @property
    def COLOR_BUNDLE_THEME_NAME(self):
        """
        Returns the name of the asset bundle for the theme's custom colors.
        This bundle includes the primary color variables that are used
        throughout the application's theme.
        Returns:
            str: The name of the theme's asset bundle.
        """
        return 'web._assets_primary_variables'
    
    #----------------------------------------------------------
    # Fields
    #----------------------------------------------------------
    
    theme_favicon = fields.Binary(
        related='company_id.favicon',
        readonly=False
    )
    
    theme_background_image = fields.Binary(
        related='company_id.background_image',
        readonly=False
    )
    
    theme_color_appsmenu_text = fields.Char(
        string='Apps Menu Text Color'
    )
    
    theme_color_appbar_text = fields.Char(
        string='AppsBar Text Color'
    )
    
    theme_color_appbar_active = fields.Char(
        string='AppsBar Active Color'
    )
    
    theme_color_appbar_background = fields.Char(
        string='AppsBar Background Color'
    )
    
    #----------------------------------------------------------
    # Helper
    #----------------------------------------------------------
    
    def _get_theme_color_values(self):
        """
        Retrieves the current color values for the theme.
        This function calls the `get_color_variables_values` method to read the
        color variables from the theme's SCSS file.
        Returns:
            dict: A dictionary of color variable names and their current values.
        """
        return self.env['web_editor.assets'].get_color_variables_values(
            self.COLOR_ASSET_THEME_URL, 
            self.COLOR_BUNDLE_THEME_NAME,
            self.THEME_COLOR_FIELDS
        )
        
    def _set_theme_color_values(self, values):
        """
        Sets the theme color values in the provided values dictionary.
        This function retrieves the current theme colors and populates the
        given dictionary with them, appending 'theme_' to the keys.
        Args:
            values (dict): The dictionary to populate with color values.
        Returns:
            dict: The updated dictionary with theme color values.
        """
        colors = self._get_theme_color_values()
        for var, value in colors.items():
            values[f'theme_{var}'] = value
        return values

    def _detect_theme_color_change(self):
        """
        Detects if any of the theme colors have been changed.
        This function compares the current color values in the settings with the
        values stored in the SCSS file.
        Returns:
            bool: True if any color has changed, False otherwise.
        """
        colors = self._get_theme_color_values()
        return any(
            self[f'theme_{var}'] != val
            for var, val in colors.items()
        )

    def _replace_theme_color_values(self):
        """
        Replaces the color values in the theme's SCSS file.
        This function takes the new color values from the settings and updates
        the SCSS file with them.
        """
        variables = [
            {
                'name': field, 
                'value': self[f'theme_{field}']
            }
            for field in self.THEME_COLOR_FIELDS
        ]
        return self.env['web_editor.assets'].replace_color_variables_values(
            self.COLOR_ASSET_THEME_URL, 
            self.COLOR_BUNDLE_THEME_NAME,
            variables
        )

    def _reset_theme_color_assets(self):
        """
        Resets the theme's color assets to their default values.
        This function restores the original SCSS file for the theme.
        """
        self.env['web_editor.assets'].reset_asset(
            self.COLOR_ASSET_THEME_URL, 
            self.COLOR_BUNDLE_THEME_NAME,
        )
    
    #----------------------------------------------------------
    # Action
    #----------------------------------------------------------
    
    def action_reset_theme_color_assets(self):
        """
        Action to reset all theme color assets.
        This function calls the methods to reset the light, dark, and theme
        color assets, and then triggers a client-side reload to apply the
        changes.
        Returns:
            dict: An action dictionary to trigger a client-side reload.
        """
        self._reset_light_color_assets()
        self._reset_dark_color_assets()
        self._reset_theme_color_assets()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------

    def get_values(self):
        """
        Extends the `get_values` method to include the theme color values.
        This function retrieves the default configuration values and then adds
        the current theme colors to the result.
        Returns:
            dict: A dictionary of configuration values, including theme colors.
        """
        res = super().get_values()
        res = self._set_theme_color_values(res)
        return res

    def set_values(self):
        """
        Extends the `set_values` method to save the theme color values.
        This function saves the default configuration values and then checks for
        changes in the theme colors. If any changes are detected, it updates
        the corresponding SCSS files.
        """
        res = super().set_values()
        if self._detect_theme_color_change():
            self._replace_theme_color_values()
        return res
