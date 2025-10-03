from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def session_info(self):
        """
        Extends the base session_info method to include the user's dialog size
        preference.
        This function retrieves the session information from the parent class
        and adds the 'dialog_size' from the current user's settings. This
        allows the client-side to be aware of the user's preferred dialog size
        (e.g., 'small', 'medium', 'large').
        Returns:
            dict: The extended session information, including the 'dialog_size'.
        """
        result = super(IrHttp, self).session_info()
        result['dialog_size'] = self.env.user.dialog_size
        return result
