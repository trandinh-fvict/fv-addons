from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def session_info(self):
        """
        Extends the base session_info method to include the user's chatter
        position preference.
        This function retrieves the session information from the parent class
        and adds the 'chatter_position' from the current user's settings.
        This allows the client-side to be aware of the user's preferred
        chatter position (e.g., 'sided' or 'normal').
        Returns:
            dict: The extended session information, including the
                  'chatter_position'.
        """
        result = super(IrHttp, self).session_info()
        result['chatter_position'] = self.env.user.chatter_position
        return result
