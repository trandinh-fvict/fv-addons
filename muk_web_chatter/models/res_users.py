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
        This property adds 'chatter_position' to the list of fields that a user
        can read on their own user record, allowing them to view their chatter
        position preference.
        Returns:
            list: A list of field names that are self-readable.
        """
        return super().SELF_READABLE_FIELDS + [
            'chatter_position',
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        """
        Extends the list of fields that are writeable by the user on their own record.
        This property adds 'chatter_position' to the list of fields that a user
        can write on their own user record, allowing them to change their
        chatter position preference.
        Returns:
            list: A list of field names that are self-writeable.
        """
        return super().SELF_WRITEABLE_FIELDS + [
            'chatter_position',
        ]

    #----------------------------------------------------------
    # Fields
    #----------------------------------------------------------
    
    chatter_position = fields.Selection(
        selection=[
            ('side', 'Side'),
            ('bottom', 'Bottom'),
        ], 
        string="Chatter Position",
        default='side',
        required=True,
    )
