# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VendorEvalVendor(models.Model):
    """
    Represents a vendor or team that can be evaluated.
    This model stores information about the vendors, including their name,
    code, and active status. It also includes a computed field to count the
    number of evaluations a vendor is a part of.
    """
    _name = 'vem.vendor'
    _description = 'Team for Evaluation'
    _order = 'name'

    name = fields.Char(
        string='Team Name',
        required=True,
        help='Name of the Team'
    )
    code = fields.Char(
        string='Team Code',
        help='Unique code for the Team'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the team'
    )
    note = fields.Text(
        string='Notes',
        help='Additional notes about the team'
    )
    evaluation_count = fields.Integer(
        string='Evaluation Count',
        compute='_compute_evaluation_count',
        help='Number of evaluations this team is part of'
    )

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Team name must be unique!'),
        ('code_unique', 'UNIQUE(code)', 'Team code must be unique!')
    ]

    @api.depends('name')
    def _compute_evaluation_count(self):
        """
        Computes the number of evaluations this vendor is a part of.
        This method counts the number of evaluation lines that are associated
        with the current vendor and sets the `evaluation_count` field
        accordingly.
        """
        for vendor in self:
            count = self.env['vem.evaluation.line'].search_count([
                ('vendor_id', '=', vendor.id)
            ])
            vendor.evaluation_count = count
