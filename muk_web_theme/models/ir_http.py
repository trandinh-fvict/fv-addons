from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    #----------------------------------------------------------
    # Functions
    #----------------------------------------------------------
    
    def session_info(self):
        """
        Extends the base session_info method to include company-specific
        information about whether a background image is available.
        This function retrieves the session information from the parent class,
        and if the user is an internal user, it iterates through the user's
        associated companies. For each company, it checks for the presence of a
        background image and adds a corresponding boolean flag to the company's
        data.
        Returns:
            dict: The extended session information, including the
                  'has_background_image' flag for each company.
        """
        result = super(IrHttp, self).session_info()
        if request.env.user._is_internal():
            for company in request.env.user.company_ids.with_context(bin_size=True):
                result['user_companies']['allowed_companies'][company.id].update({
                    'has_background_image': bool(company.background_image),
                })
        return result
