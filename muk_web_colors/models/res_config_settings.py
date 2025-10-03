from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    # ----------------------------------------------------------
    # Properties
    # ----------------------------------------------------------

    @property
    def COLOR_FIELDS(self):
        """
        Returns a list of the color fields that can be customized.
        These fields correspond to the different color variables used in the
        application's theme, such as brand, primary, success, etc.
        Returns:
            list: A list of color field names.
        """
        return [
            'color_brand',
            'color_primary',
            'color_success',
            'color_info',
            'color_warning',
            'color_danger',
        ]
        
    @property
    def COLOR_ASSET_LIGHT_URL(self):
        """
        Returns the URL of the SCSS file for the light color theme.
        This file contains the color variables that will be modified when
        customizing the light theme.
        Returns:
            str: The URL of the light theme SCSS file.
        """
        return '/muk_web_colors/static/src/scss/colors_light.scss'
        
    @property
    def COLOR_BUNDLE_LIGHT_NAME(self):
        """
        Returns the name of the asset bundle for the light theme.
        This bundle includes the primary color variables that are used
        throughout the application's light theme.
        Returns:
            str: The name of the light theme asset bundle.
        """
        return 'web._assets_primary_variables'
        
    @property
    def COLOR_ASSET_DARK_URL(self):
        """
        Returns the URL of the SCSS file for the dark color theme.
        This file contains the color variables that will be modified when
        customizing the dark theme.
        Returns:
            str: The URL of the dark theme SCSS file.
        """
        return '/muk_web_colors/static/src/scss/colors_dark.scss'
        
    @property
    def COLOR_BUNDLE_DARK_NAME(self):
        """
        Returns the name of the asset bundle for the dark theme.
        This bundle includes the color variables that are used throughout the
        application's dark theme.
        Returns:
            str: The name of the dark theme asset bundle.
        """
        return 'web.assets_web_dark'

    #----------------------------------------------------------
    # Fields Light Mode
    #----------------------------------------------------------
    
    color_brand_light = fields.Char(
        string='Brand Light Color'
    )
    
    color_primary_light = fields.Char(
        string='Primary Light Color'
    )
    
    color_success_light = fields.Char(
        string='Success Light Color'
    )
    
    color_info_light = fields.Char(
        string='Info Light Color'
    )
    
    color_warning_light = fields.Char(
        string='Warning Light Color'
    )
    
    color_danger_light = fields.Char(
        string='Danger Light Color'
    )

    #----------------------------------------------------------
    # Fields Dark Mode
    #----------------------------------------------------------
    
    color_brand_dark = fields.Char(
        string='Brand Dark Color'
    )
    
    color_primary_dark = fields.Char(
        string='Primary Dark Color'
    )
    
    color_success_dark = fields.Char(
        string='Success Dark Color'
    )
    
    color_info_dark = fields.Char(
        string='Info Dark Color'
    )
    
    color_warning_dark = fields.Char(
        string='Warning Dark Color'
    )
    
    color_danger_dark = fields.Char(
        string='Danger Dark Color'
    )
    
    #----------------------------------------------------------
    # Helper
    #----------------------------------------------------------
    
    def _get_light_color_values(self):
        """
        Retrieves the current color values for the light theme.
        This function calls the `get_color_variables_values` method to read the
        color variables from the light theme's SCSS file.
        Returns:
            dict: A dictionary of color variable names and their current values.
        """
        return self.env['web_editor.assets'].get_color_variables_values(
            self.COLOR_ASSET_LIGHT_URL, 
            self.COLOR_BUNDLE_LIGHT_NAME,
            self.COLOR_FIELDS
        )
        
    def _get_dark_color_values(self):
        """
        Retrieves the current color values for the dark theme.
        This function calls the `get_color_variables_values` method to read the
        color variables from the dark theme's SCSS file.
        Returns:
            dict: A dictionary of color variable names and their current values.
        """
        return self.env['web_editor.assets'].get_color_variables_values(
            self.COLOR_ASSET_DARK_URL, 
            self.COLOR_BUNDLE_DARK_NAME,
            self.COLOR_FIELDS
        )
        
    def _set_light_color_values(self, values):
        """
        Sets the light color values in the provided values dictionary.
        This function retrieves the current light theme colors and populates the
        given dictionary with them, appending '_light' to the keys.
        Args:
            values (dict): The dictionary to populate with color values.
        Returns:
            dict: The updated dictionary with light color values.
        """
        colors = self._get_light_color_values()
        for var, value in colors.items():
            values[f'{var}_light'] = value
        return values
        
    def _set_dark_color_values(self, values):
        """
        Sets the dark color values in the provided values dictionary.
        This function retrieves the current dark theme colors and populates the
        given dictionary with them, appending '_dark' to the keys.
        Args:
            values (dict): The dictionary to populate with color values.
        Returns:
            dict: The updated dictionary with dark color values.
        """
        colors = self._get_dark_color_values()
        for var, value in colors.items():
            values[f'{var}_dark'] = value
        return values
    
    def _detect_light_color_change(self):
        """
        Detects if any of the light theme colors have been changed.
        This function compares the current color values in the settings with the
        values stored in the SCSS file.
        Returns:
            bool: True if any color has changed, False otherwise.
        """
        colors = self._get_light_color_values()
        return any(
            self[f'{var}_light'] != val
            for var, val in colors.items()
        )
        
    def _detect_dark_color_change(self):
        """
        Detects if any of the dark theme colors have been changed.
        This function compares the current color values in the settings with the
        values stored in the SCSS file.
        Returns:
            bool: True if any color has changed, False otherwise.
        """
        colors = self._get_dark_color_values()
        return any(
            self[f'{var}_dark'] != val
            for var, val in colors.items()
        )
        
    def _replace_light_color_values(self):
        """
        Replaces the color values in the light theme's SCSS file.
        This function takes the new color values from the settings and updates
        the SCSS file with them.
        """
        variables = [
            {
                'name': field, 
                'value': self[f'{field}_light']
            }
            for field in self.COLOR_FIELDS
        ]
        return self.env['web_editor.assets'].replace_color_variables_values(
            self.COLOR_ASSET_LIGHT_URL, 
            self.COLOR_BUNDLE_LIGHT_NAME,
            variables
        )
        
    def _replace_dark_color_values(self):
        """
        Replaces the color values in the dark theme's SCSS file.
        This function takes the new color values from the settings and updates
        the SCSS file with them.
        """
        variables = [
            {
                'name': field, 
                'value': self[f'{field}_dark']
            }
            for field in self.COLOR_FIELDS
        ]
        return self.env['web_editor.assets'].replace_color_variables_values(
            self.COLOR_ASSET_DARK_URL, 
            self.COLOR_BUNDLE_DARK_NAME,
            variables
        )
    
    def _reset_light_color_assets(self):
        """
        Resets the light theme's color assets to their default values.
        This function restores the original SCSS file for the light theme.
        """
        self.env['web_editor.assets'].reset_color_asset(
            self.COLOR_ASSET_LIGHT_URL, 
            self.COLOR_BUNDLE_LIGHT_NAME,
        )
        
    def _reset_dark_color_assets(self):
        """
        Resets the dark theme's color assets to their default values.
        This function restores the original SCSS file for the dark theme.
        """
        self.env['web_editor.assets'].reset_asset(
            self.COLOR_ASSET_DARK_URL, 
            self.COLOR_BUNDLE_DARK_NAME,
        )
        
    #----------------------------------------------------------
    # Action
    #----------------------------------------------------------
    
    def action_reset_light_color_assets(self):
        """
        Action to reset the light theme's color assets.
        This function calls the `_reset_light_color_assets` method and then
        triggers a client-side reload to apply the changes.
        Returns:
            dict: An action dictionary to trigger a client-side reload.
        """
        self._reset_light_color_assets()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_reset_dark_color_assets(self):
        """
        Action to reset the dark theme's color assets.
        This function calls the `_reset_dark_color_assets` method and then
        triggers a client-side reload to apply the changes.
        Returns:
            dict: An action dictionary to trigger a client-side reload.
        """
        self._reset_dark_color_assets()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------

    def get_values(self):
        """
        Extends the `get_values` method to include the light and dark theme
        color values.
        This function retrieves the default configuration values and then adds
        the current light and dark theme colors to the result.
        Returns:
            dict: A dictionary of configuration values, including theme colors.
        """
        res = super().get_values()
        res = self._set_light_color_values(res)
        res = self._set_dark_color_values(res)
        return res

    def set_values(self):
        """
        Extends the `set_values` method to save the light and dark theme color
        values.
        This function saves the default configuration values and then checks for
        changes in the light and dark theme colors. If any changes are
        detected, it updates the corresponding SCSS files.
        """
        res = super().set_values()
        if self._detect_light_color_change():
            self._replace_light_color_values()
        if self._detect_dark_color_change():
            self._replace_dark_color_values()
        return res
