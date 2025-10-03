# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SuggestionCategory(models.Model):
    _name = 'suggestion.category'
    _description = 'Suggestion Category'
    _parent_store = True

    name = fields.Char(required=True)
    level = fields.Selection([
        ('category', 'Category'),
        ('area', 'Area'),
        ('item', 'Item'),
    ], required=True)
    parent_id = fields.Many2one('suggestion.category', 'Parent', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    _sql_constraints = [
        ('uniq_name_parent_level', 'unique(name, parent_id, level)', 'The combination of name, parent, and level must be unique.')
    ]

class SuggestionSuggestion(models.Model):
    _name = 'suggestion.suggestion'
    _description = 'Suggestion'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    category_id = fields.Many2one('suggestion.category', 'Category', domain="[('level','=','category')]", tracking=True)
    area_id = fields.Many2one('suggestion.category', 'Area', domain="[('level','=','area')]", tracking=True)
    item_id = fields.Many2one('suggestion.category', 'Item', domain="[('level','=','item')]", tracking=True)
    description = fields.Text()
    image = fields.Binary(attachment=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='new', tracking=True, group_expand='_read_group_stage_ids')
    owner_id = fields.Many2one('res.users', 'Owner', default=lambda self: self.env.user)
    assigned_id = fields.Many2one('res.users', 'Assigned To')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
    ], default='1')
    active = fields.Boolean(default=True)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = self._fields['state'].get_values(self.env)
        return [s[0] for s in stage_ids]

    def action_start(self):
        for rec in self:
            if not rec.assigned_id:
                rec.assigned_id = self.env.user
            rec.state = 'in_progress'
            rec.message_post_with_template(self.env.ref('suggestion_box.email_template_suggestion_status_change').id)


    def action_done(self):
        for rec in self:
            rec.state = 'done'
            rec.message_post_with_template(self.env.ref('suggestion_box.email_template_suggestion_status_change').id)

    @api.model
    def create(self, vals):
        res = super(SuggestionSuggestion, self).create(vals)
        if res.owner_id:
            res.message_post_with_template(self.env.ref('suggestion_box.email_template_suggestion_acknowledgement').id)

        # Schedule follow-up activity
        self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('suggestion_box.activity_suggestion_follow_up').id,
            'res_id': res.id,
            'res_model_id': self.env.ref('suggestion_box.model_suggestion_suggestion').id,
            'user_id': res.assigned_id.id or (self.env.ref('suggestion_box.group_suggestion_manager').users and self.env.ref('suggestion_box.group_suggestion_manager').users[0].id) or self.env.user.id
        })
        return res

    def _cron_escalate(self):
        manager_group = self.env.ref('suggestion_box.group_suggestion_manager')
        managers = manager_group.users
        for suggestion in self:
            suggestion.priority = '2' # High
            suggestion.message_post(body="This suggestion has been escalated due to being stale.", subtype_xmlid="mail.mt_note", partner_ids=managers.mapped('partner_id').ids)


    @api.onchange('category_id')
    def _onchange_category_id(self):
        self.area_id = False
        if self.category_id:
            return {'domain': {'area_id': [('parent_id', '=', self.category_id.id), ('level', '=', 'area')]}}
        return {'domain': {'area_id': []}}

    @api.onchange('area_id')
    def _onchange_area_id(self):
        self.item_id = False
        if self.area_id:
            return {'domain': {'item_id': [('parent_id', '=', self.area_id.id), ('level', '=', 'item')]}}
        return {'domain': {'item_id': []}}

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_anonymous = fields.Boolean(string="Allow Anonymous Suggestions", config_parameter='suggestion_box.allow_anonymous')
    default_responsible_id = fields.Many2one('res.users', string="Default Responsible", config_parameter='suggestion_box.default_responsible_id')
    sla_days = fields.Integer(string="SLA Days", config_parameter='suggestion_box.sla_days')
    email_alias = fields.Char(string="Email Alias", config_parameter='suggestion_box.email_alias')