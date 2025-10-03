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
        This property adds 'sidebar_type' to the list of fields that a user can
        read on their own user record, allowing them to view their sidebar
        preference.
        Returns:
            list: A list of field names that are self-readable.
        """
        return super().SELF_READABLE_FIELDS + [
            'sidebar_type',
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        """
        Extends the list of fields that are writeable by the user on their own record.
        This property adds 'sidebar_type' to the list of fields that a user can
        write on their own user record, allowing them to change their sidebar
        preference.
        Returns:
            list: A list of field names that are self-writeable.
        """
        return super().SELF_WRITEABLE_FIELDS + [
            'sidebar_type',
        ]

    #----------------------------------------------------------
    # Fields
    #----------------------------------------------------------
    
    sidebar_type = fields.Selection(
        selection=[
            ('invisible', 'Invisible'),
            ('small', 'Small'),
            ('large', 'Large')
        ], 
        string="Sidebar Type",
        default='large',
        required=True,
    )
