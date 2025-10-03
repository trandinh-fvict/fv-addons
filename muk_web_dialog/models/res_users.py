from odoo import models, fields, api


class ResUsers(models.Model):
    
    _inherit = 'res.users'
    
    #----------------------------------------------------------
    # Properties
    #----------------------------------------------------------
    
    @property
    def SELF_READABLE_FIELDS(self):
        """
        Extends the list of fields that are readable by the user on their own record.
        This property adds 'dialog_size' to the list of fields that a user can
        read on their own user record, allowing them to view their dialog size
        preference.
        Returns:
            list: A list of field names that are self-readable.
        """
        return super().SELF_READABLE_FIELDS + [
            'dialog_size',
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        """
        Extends the list of fields that are writeable by the user on their own record.
        This property adds 'dialog_size' to the list of fields that a user can
        write on their own user record, allowing them to change their dialog
        size preference.
        Returns:
            list: A list of field names that are self-writeable.
        """
        return super().SELF_WRITEABLE_FIELDS + [
            'dialog_size',
        ]

    #----------------------------------------------------------
    # Fields
    #----------------------------------------------------------
    
    dialog_size = fields.Selection(
        selection=[
            ('minimize', 'Minimize'),
            ('maximize', 'Maximize'),
        ], 
        string="Dialog Size",
        default='minimize',
        required=True,
    )
