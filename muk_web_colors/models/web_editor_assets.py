import re
import base64

from odoo import models, fields, api
from odoo.tools import misc

from odoo.addons.base.models.assetsbundle import EXTENSIONS


class ScssEditor(models.AbstractModel):
    
    _inherit = 'web_editor.assets'

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    @api.model
    def _get_colors_attachment(self, custom_url):
        """
        Retrieves an attachment based on its custom URL.
        This function searches for an 'ir.attachment' record that has a URL
        matching the provided custom URL.
        Args:
            custom_url (str): The custom URL of the attachment to find.
        Returns:
            recordset: A recordset containing the found attachment, or an empty
                       recordset if not found.
        """
        return self.env['ir.attachment'].search([
            ('url', '=', custom_url)
        ])

    @api.model
    def _get_colors_asset(self, custom_url):
        """
        Retrieves an asset based on its custom URL.
        This function searches for an 'ir.asset' record that has a path
        matching the provided custom URL.
        Args:
            custom_url (str): The custom URL of the asset to find.
        Returns:
            recordset: A recordset containing the found asset, or an empty
                       recordset if not found.
        """
        return self.env['ir.asset'].search([
            ('path', 'like', custom_url)
        ])

    @api.model
    def _get_colors_from_url(self, url, bundle):
        """
        Retrieves the content of a color asset from a given URL.
        This function first checks if a customized version of the asset exists
        as an attachment. If so, it returns the content of the attachment.
        Otherwise, it reads the content from the original file.
        Args:
            url (str): The URL of the color asset.
            bundle (str): The name of the asset bundle.
        Returns:
            bytes: The content of the color asset.
        """
        custom_url = self._make_custom_asset_url(url, bundle)
        url_info = self._get_data_from_url(custom_url)
        if url_info['customized']:
            attachment = self._get_colors_attachment(
                custom_url
            )
            if attachment:
                return base64.b64decode(attachment.datas)
        with misc.file_open(url.strip('/'), 'rb', filter_ext=EXTENSIONS) as f:
            return f.read()

    def _get_color_variable(self, content, variable):
        """
        Extracts the value of a single color variable from a string of content.
        This function uses a regular expression to find the value of a specific
        color variable (e.g., '$mk_color_brand').
        Args:
            content (str): The string content to search within.
            variable (str): The name of the color variable to find.
        Returns:
            str or None: The value of the color variable, or None if not found.
        """
        value = re.search(fr'\$mk_{variable}\:?\s(.*?);', content)
        return value and value.group(1)

    def _get_color_variables(self, content, variables):
        """
        Extracts the values of multiple color variables from a string of content.
        This function iterates through a list of variable names and calls
        `_get_color_variable` for each one.
        Args:
            content (str): The string content to search within.
            variables (list): A list of color variable names to find.
        Returns:
            dict: A dictionary mapping variable names to their values.
        """
        return {
            var: self._get_color_variable(content, var) 
            for var in variables
        }

    def _replace_color_variables(self, content, variables):
        """
        Replaces the values of multiple color variables in a string of content.
        This function iterates through a list of variables and their new values,
        and replaces the old values with the new ones in the content string.
        Args:
            content (str): The string content to modify.
            variables (list): A list of dictionaries, each containing the 'name'
                              and 'value' of a color variable to replace.
        Returns:
            str: The modified content string.
        """
        for variable in variables:
            content = re.sub(
                fr'{variable["name"]}\:?\s(.*?);', 
                f'{variable["name"]}: {variable["value"]};', 
                content
            )
        return content

    @api.model
    def _save_color_asset(self, url, bundle, content):
        """
        Saves the modified color asset as a new attachment.
        This function creates a new 'ir.attachment' and 'ir.asset' record to
        store the customized version of the color asset. If a custom asset
        already exists, it updates the existing record.
        Args:
            url (str): The original URL of the color asset.
            bundle (str): The name of the asset bundle.
            content (str): The modified content of the color asset.
        """
        custom_url = self._make_custom_asset_url(url, bundle)
        asset_url = url[1:] if url.startswith(('/', '\\')) else url
        datas = base64.b64encode((content or "\n").encode("utf-8"))
        custom_attachment = self._get_colors_attachment(
            custom_url
        )
        if custom_attachment:
            custom_attachment.write({"datas": datas})
            self.env.registry.clear_cache('assets')
        else:
            attachment_values = {
                'name': url.split("/")[-1],
                'type': "binary",
                'mimetype': 'text/scss',
                'datas': datas,
                'url': custom_url,
            }
            asset_values = {
                'path': custom_url,
                'target': url,
                'directive': 'replace',
            }
            target_asset = self._get_colors_asset(
                asset_url
            )
            if target_asset:
                asset_values['name'] = '%s override' % target_asset.name
                asset_values['bundle'] = target_asset.bundle
                asset_values['sequence'] = target_asset.sequence
            else:
                asset_values['name'] = '%s: replace %s' % (
                    bundle, custom_url.split('/')[-1]
                )
                asset_values['bundle'] = self.env['ir.asset']._get_related_bundle(
                    url, bundle
                )
            self.env['ir.attachment'].create(attachment_values)
            self.env['ir.asset'].create(asset_values)

    # ----------------------------------------------------------
    # Functions
    # ----------------------------------------------------------

    def get_color_variables_values(self, url, bundle, variables):
        """
        Retrieves the values of specified color variables from a given asset URL.
        This function reads the content of the asset, decodes it, and then extracts
        the values of the specified color variables.
        Args:
            url (str): The URL of the color asset.
            bundle (str): The name of the asset bundle.
            variables (list): A list of color variable names to retrieve.
        Returns:
            dict: A dictionary mapping variable names to their values.
        """
        content = self._get_colors_from_url(url, bundle)
        return self._get_color_variables(
            content.decode('utf-8'), variables
        )
    
    def replace_color_variables_values(self, url, bundle, variables):
        """
        Replaces the values of specified color variables in a given asset URL.
        This function reads the original content of the asset, replaces the
        color variables with new values, and then saves the modified content
        as a new asset.
        Args:
            url (str): The URL of the color asset.
            bundle (str): The name of the asset bundle.
            variables (list): A list of dictionaries, each containing the 'name'
                              and 'value' of a color variable to replace.
        """
        original = self._get_colors_from_url(url, bundle).decode('utf-8')
        content = self._replace_color_variables(original, variables)
        self._save_color_asset(url, bundle, content)

    def reset_color_asset(self, url, bundle):
        """
        Resets a customized color asset to its original state.
        This function deletes the attachment and asset records associated with
        the customized version of the color asset, effectively restoring the
        original file.
        Args:
            url (str): The URL of the color asset to reset.
            bundle (str): The name of the asset bundle.
        """
        custom_url = self._make_custom_asset_url(url, bundle)
        self._get_colors_attachment(custom_url).unlink()
        self._get_colors_asset(custom_url).unlink()
