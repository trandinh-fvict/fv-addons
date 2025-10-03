# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import json


class VendorEvalQuestion(models.Model):
    """
    Represents an evaluation question used in the vendor evaluation matrix.
    This model stores the questions that are used to evaluate vendors, along
    with their sequence and active status.
    """
    _name = 'vem.eval.question'
    _description = 'Evaluation Question'
    _order = 'sequence, id'

    name = fields.Text(
        string='Question',
        required=True,
        help='Content of the evaluation question'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=1,
        help='Order of the question in evaluation'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the question'
    )


class VendorEvaluation(models.Model):
    """
    Represents a vendor evaluation, which is a collection of scores for
    multiple vendors across a set of questions.
    This model manages the entire evaluation process, from creation to
    submission and approval. It also includes methods for calculating total
    scores, generating summary data, and handling the evaluation matrix view.
    """
    _name = 'vem.evaluation'
    _description = 'Team Evaluation'
    _order = 'create_date desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Evaluation Name',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    evaluator_name = fields.Char(
        string='Evaluator Name',
        required=True,
        help='Name of the person performing the evaluation'
    )
    vendor_ids = fields.Many2many(
        'vem.vendor',
        string='Team to Evaluate',
        required=True,
        help='Select Team to be evaluated'
    )
    line_ids = fields.One2many(
        'vem.evaluation.line',
        'evaluation_id',
        string='Evaluation Lines'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted')
    ], string='State', default='draft', tracking=True)

    create_date = fields.Datetime(string='Creation Date', readonly=True)
    submit_date = fields.Datetime(string='Submit Date', readonly=True)
    approve_date = fields.Datetime(string='Approve Date', readonly=True)

    total_scores = fields.Text(
        string='Total Scores JSON',
        compute='_compute_total_scores',
        store=True,
        help='JSON storage of total scores by FV'
    )

    line_count = fields.Integer(
        string='Lines Count',
        compute='_compute_line_count'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to assign a unique sequence number to each
        new evaluation.
        This ensures that each evaluation has a unique name based on the
        'vem.evaluation' sequence.
        Args:
            vals_list (list): A list of dictionaries of values to create new
                              records.
        Returns:
            recordset: The newly created evaluation records.
        """
        for vals in vals_list:
            if vals.get('name', ' ') == ' ':
                vals['name'] = self.env['ir.sequence'].next_by_code('vem.evaluation') or ' '
        return super().create(vals_list)

    @api.depends('line_ids.score')
    def _compute_total_scores(self):
        """
        Computes the total scores for each vendor in the evaluation and stores
        them as a JSON string.
        This method calculates the total score, max possible score, and the
        percentage score for each vendor and stores the result in the
        `total_scores` field.
        """
        for evaluation in self:
            totals = {}
            for vendor in evaluation.vendor_ids:
                lines = evaluation.line_ids.filtered(lambda l: l.vendor_id.id == vendor.id)
                total_score = sum(lines.mapped('score'))
                totals[vendor.id] = {
                    'vendor_name': vendor.name,
                    'total_score': total_score,
                    'max_score': len(evaluation.line_ids.mapped('question_id')) * 5 if evaluation.line_ids else 85,
                    'percentage': round((total_score / 85) * 100, 2) if total_score > 0 else 0
                }
            evaluation.total_scores = json.dumps(totals)

    @api.depends('line_ids')
    def _compute_line_count(self):
        """
        Computes the total number of evaluation lines for the current evaluation.
        This method is used to display the number of lines in the evaluation
        form view.
        """
        for evaluation in self:
            evaluation.line_count = len(evaluation.line_ids)

    @api.onchange('vendor_ids')
    def _onchange_vendor_ids(self):
        """
        Handles the onchange event for the `vendor_ids` field.
        When the list of vendors to be evaluated changes, this method triggers
        the creation of new evaluation lines for the added vendors.
        """
        if self.vendor_ids and self._origin.id:
            self._create_evaluation_lines()

    def _create_evaluation_lines(self):
        """
        Creates evaluation lines for all combinations of questions and vendors.
        This method ensures that an evaluation line exists for each active
        question and each selected vendor. It only creates lines that do not
        already exist, preserving any existing scores.
        """
        if not self.vendor_ids:
            return

        # Get all questions
        questions = self.env['vem.eval.question'].search([('active', '=', True)])

        # Only create missing lines, don't remove existing ones
        lines_to_create = []
        for question in questions:
            for vendor in self.vendor_ids:
                # Check if line already exists
                existing_line = self.line_ids.filtered(
                    lambda l: l.question_id.id == question.id and l.vendor_id.id == vendor.id
                )

                # Only create if line doesn't exist
                if not existing_line:
                    lines_to_create.append({
                        'evaluation_id': self.id,
                        'question_id': question.id,
                        'vendor_id': vendor.id,
                        'score': 1,  # Default score
                    })

        if lines_to_create:
            self.env['vem.evaluation.line'].create(lines_to_create)

    def action_open_matrix(self):
        """
        Opens the evaluation matrix view in a new browser tab.
        This action ensures that at least one vendor is selected, creates any
        missing evaluation lines, and then redirects the user to the
        evaluation matrix page.
        Returns:
            dict: An action dictionary to open the evaluation matrix URL.
        """
        self.ensure_one()
        if not self.vendor_ids:
            raise UserError("Please select at least one vendor before opening the evaluation matrix.")

        # Only create missing evaluation lines, preserve existing scores
        self._create_evaluation_lines()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/vem/eval/{self.id}',
            'target': 'self',
        }

    def action_submit(self):
        """
        Submits the evaluation and sets its state to 'submitted'.
        This action validates that all evaluation lines have been filled in
        with valid scores before changing the state. Once submitted, the
        evaluation is considered final and approved.
        """
        self.ensure_one()

        # Refresh data to ensure we have latest scores
        self.env.invalidate_all()

        if not self.line_ids:
            raise UserError("No evaluation data found. Please complete the evaluation first.")

        # Check if all vendors have at least some scores
        total_expected_lines = len(self.vendor_ids) * len(self.env['vem.eval.question'].search([('active', '=', True)]))

        if len(self.line_ids) < total_expected_lines:
            raise UserError("Please complete all evaluation scores before submitting.")

        # Check if all scores are valid
        invalid_scores = self.line_ids.filtered(lambda l: not l.score or l.score < 1 or l.score > 5)
        if invalid_scores:
            raise UserError("All evaluation scores must be between 1 and 5 before submitting.")

        # Update state - submitted is now the final approved state
        self.write({
            'state': 'submitted',
            'submit_date': fields.Datetime.now()
        })

    def action_reset_to_draft(self):
        """
        Resets the evaluation back to the 'draft' state.
        This action allows a submitted or approved evaluation to be moved back
        to the draft state, so that it can be modified again.
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'submit_date': False,
            'approve_date': False
        })

    def get_summary_data(self):
        """
        Retrieves structured data for the evaluation summary report.
        This method compiles all the necessary data for a single evaluation
        summary, including information about the evaluator, teams, questions,
        and scores.
        Returns:
            dict: A dictionary containing the structured summary data.
        """
        self.ensure_one()

        # Get all evaluators (people who scored)
        evaluators = self.env['vem.evaluation'].search([
            ('id', 'in', self.ids)
        ]).mapped('evaluator_name')

        # Get all teams
        teams = self.vendor_ids

        # Get all questions
        questions = self.env['vem.eval.question'].search([('active', '=', True)], order='sequence')

        # Prepare summary data structure
        summary_data = {
            'evaluation': self,
            'teams': teams,
            'questions': questions,
            'evaluators': [],
            'team_totals': {},
            'grand_total': 0
        }

        # For single evaluation, use current evaluator
        evaluator_data = {
            'name': self.evaluator_name,
            'team_scores': {},
            'total': 0
        }

        # Calculate scores for each team
        for team in teams:
            team_lines = self.line_ids.filtered(lambda l: l.vendor_id.id == team.id)
            team_score = sum(team_lines.mapped('score'))
            evaluator_data['team_scores'][team.id] = team_score
            evaluator_data['total'] += team_score

            # Update team totals
            if team.id not in summary_data['team_totals']:
                summary_data['team_totals'][team.id] = 0
            summary_data['team_totals'][team.id] += team_score

        summary_data['evaluators'].append(evaluator_data)
        summary_data['grand_total'] = evaluator_data['total']

        return summary_data

    @api.model
    def get_multi_evaluation_summary(self, evaluation_ids):
        """
        Retrieves summary data for multiple evaluations.
        This method compiles all the necessary data for a multi-evaluation
        summary, including information about all evaluators, teams, questions,
        and scores.
        Args:
            evaluation_ids (list): A list of IDs of the evaluations to include
                                   in the summary.
        Returns:
            dict: A dictionary containing the structured summary data.
        """
        evaluations = self.browse(evaluation_ids)

        if not evaluations.exists():
            return {}

        # Get all teams from selected evaluations
        all_teams = evaluations.mapped('vendor_ids')

        # Get all questions
        questions = self.env['vem.eval.question'].search([('active', '=', True)], order='sequence')

        # Prepare summary data structure
        summary_data = {
            'evaluations': evaluations,
            'teams': all_teams,
            'questions': questions,
            'evaluators': [],
            'team_totals': {team.id: 0 for team in all_teams},
            'grand_total': 0
        }

        # Process each evaluation (each evaluator)
        for evaluation in evaluations:
            evaluator_data = {
                'name': evaluation.evaluator_name,
                'evaluation_id': evaluation.id,
                'team_scores': {},
                'total': 0
            }

            # Calculate scores for each team
            for team in all_teams:
                team_lines = evaluation.line_ids.filtered(lambda l: l.vendor_id.id == team.id)
                team_score = sum(team_lines.mapped('score')) if team_lines else 0
                evaluator_data['team_scores'][team.id] = team_score
                evaluator_data['total'] += team_score

                # Update team totals
                summary_data['team_totals'][team.id] += team_score

            summary_data['evaluators'].append(evaluator_data)
            summary_data['grand_total'] += evaluator_data['total']

        return summary_data

    def action_summary_preview(self):
        """
        Opens a summary preview for multiple evaluations in a new browser tab.
        This action generates a URL for the multi-evaluation summary page and
        returns an action dictionary to open the URL.
        Returns:
            dict: An action dictionary to open the summary preview URL.
        """
        evaluation_ids = self.ids

        if not evaluation_ids:
            raise UserError("Vui lòng chọn ít nhất một đánh giá để xem tổng hợp.")

        # Convert IDs to string for URL
        ids_str = ','.join(map(str, evaluation_ids))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/vem/tpm_summary?evaluation_ids={ids_str}',
            'target': 'new',
        }

    @api.model
    def save_score(self, evaluation_id, question_id, vendor_id, score):
        """
        Saves a score for a specific evaluation, question, and vendor.
        This method is designed to be called from the client-side to save
        scores asynchronously. It performs validation to ensure that the
        evaluation is in the correct state and that the score is valid.
        Args:
            evaluation_id (int): The ID of the evaluation.
            question_id (int): The ID of the question.
            vendor_id (int): The ID of the vendor.
            score (int or float): The score to be saved.
        Returns:
            dict: A dictionary indicating the success or failure of the
                  operation.
        """
        try:
            evaluation = self.browse(evaluation_id)

            # Validate evaluation state
            if evaluation.state != 'draft':
                return {'error': 'Cannot modify submitted evaluation'}

            # Validate score
            if not isinstance(score, (int, float)) or score < 1 or score > 5:
                return {'error': 'Score must be between 1 and 5'}

            # Find existing line or create new one
            line = self.env['vem.evaluation.line'].search([
                ('evaluation_id', '=', evaluation_id),
                ('question_id', '=', question_id),
                ('vendor_id', '=', vendor_id)
            ], limit=1)

            if line:
                line.write({'score': score})
            else:
                self.env['vem.evaluation.line'].create({
                    'evaluation_id': evaluation_id,
                    'question_id': question_id,
                    'vendor_id': vendor_id,
                    'score': score
                })

            # Trigger recomputation of total scores
            evaluation._compute_total_scores()

            return {'success': True}

        except Exception as e:
            # Log error for debugging
            _logger.error("Error saving score: %s", str(e), exc_info=True)
            return {'error': str(e)}


class VendorEvaluationLine(models.Model):
    """
    Represents a single line in a vendor evaluation, corresponding to a score
    for a specific question and vendor.
    This model stores the individual scores that make up a vendor evaluation.
    It includes constraints to ensure data integrity, such as a valid score
    range and uniqueness of the evaluation-question-vendor combination.
    """
    _name = 'vem.evaluation.line'
    _description = 'Vendor Evaluation Line'
    _order = 'evaluation_id, question_id, vendor_id'

    evaluation_id = fields.Many2one(
        'vem.evaluation',
        string='Evaluation',
        required=True,
        ondelete='cascade',
        help='Reference to the evaluation'
    )
    question_id = fields.Many2one(
        'vem.eval.question',
        string='Question',
        required=True,
        help='The evaluation question'
    )
    vendor_id = fields.Many2one(
        'vem.vendor',
        string='Team',
        required=True,
        help='The team being evaluated'
    )
    score = fields.Integer(
        string='Score',
        required=True,
        default=1,
        help='Score from 1 to 5'
    )

    # Computed fields for the views
    question_sequence = fields.Integer(
        string='Question Sequence',
        related='question_id.sequence',
        store=True
    )
    question_name = fields.Text(
        string='Question',
        related='question_id.name',
        store=True
    )
    vendor_name = fields.Char(
        string='Team Name',
        related='vendor_id.name',
        store=True
    )

    _sql_constraints = [
        ('score_range', 'CHECK(score >= 1 AND score <= 5)', 'Score must be between 1 and 5!'),
        ('unique_evaluation_question_vendor', 'UNIQUE(evaluation_id, question_id, vendor_id)',
         'Only one score per question per vendor per evaluation!')
    ]

    @api.constrains('score')
    def _check_score(self):
        """
        Validates that the score is within the allowed range of 1 to 5.
        This constraint ensures that all scores entered into the system are
        valid.
        """
        for line in self:
            if line.score < 1 or line.score > 5:
                raise ValidationError("Score must be between 1 and 5")
