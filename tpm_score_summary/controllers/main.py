# -*- coding: utf-8 -*-

import json
import logging
import time
from collections import defaultdict
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)

# Rate limiting storage
_rate_limit_storage = defaultdict(list)
_rate_limit_window = 60  # seconds
_rate_limit_max_requests = 100  # max requests per window (increased from 30)


class VendorEvaluationController(http.Controller):

    def _check_rate_limit(self, user_id):
        """
        Checks if a user has exceeded the rate limit for requests.
        This function implements a simple rate limiting mechanism to prevent
        abuse from rapid-fire requests. It tracks the number of requests made
        by a user within a specific time window and blocks further requests if
        the limit is exceeded.
        Args:
            user_id (int): The ID of the user to check.
        Returns:
            bool: True if the user is within the rate limit, False otherwise.
        """
        current_time = time.time()
        user_requests = _rate_limit_storage[user_id]

        # Remove old requests outside the window
        _rate_limit_storage[user_id] = [
            req_time for req_time in user_requests
            if current_time - req_time < _rate_limit_window
        ]

        # Check if user has exceeded rate limit
        if len(_rate_limit_storage[user_id]) >= _rate_limit_max_requests:
            _logger.warning(f"Rate limit exceeded for user {user_id}: {len(_rate_limit_storage[user_id])} requests")
            return False

        # Add current request
        _rate_limit_storage[user_id].append(current_time)
        return True

    @http.route('/vem/eval/<int:evaluation_id>', type='http', auth='user', website=True)
    def evaluation_matrix(self, evaluation_id, **kwargs):
        """
        Displays the evaluation matrix for a specific evaluation.
        This function retrieves the evaluation record, checks for access
        rights, and then prepares the data needed to render the evaluation
        matrix template. This includes the list of questions, the matrix data,
        and the total scores for each vendor.
        Args:
            evaluation_id (int): The ID of the evaluation to display.
            **kwargs: Additional keyword arguments.
        Returns:
            odoo.http.Response: The rendered evaluation matrix template.
        """
        try:
            # Get the evaluation record
            evaluation = request.env['vem.evaluation'].browse(evaluation_id)

            # Check if evaluation exists and user has access
            if not evaluation.exists():
                return request.render('http_routing.404')

            # Check access rights - use only check_access for Odoo 18
            evaluation.check_access('read')

            # Get all questions
            questions = request.env['vem.eval.question'].search([('active', '=', True)], order='sequence, id')

            # Prepare matrix data (question_id, vendor_id) -> line
            matrix_data = {}
            vendor_totals = {}

            # Initialize vendor totals
            for vendor in evaluation.vendor_ids:
                vendor_totals[vendor.id] = 0

            # Populate matrix data and calculate totals
            for line in evaluation.line_ids:
                key = (line.question_id.id, line.vendor_id.id)
                matrix_data[key] = line
                vendor_totals[line.vendor_id.id] += line.score

            # Prepare template values
            values = {
                'evaluation': evaluation,
                'questions': questions,
                'matrix_data': matrix_data,
                'vendor_totals': vendor_totals,
            }

            return request.render('tpm_score_summary.evaluation_matrix_template', values)

        except AccessError:
            return request.render('http_routing.403')
        except Exception as e:
            _logger.error("Error displaying evaluation matrix: %s", str(e))
            return request.render('http_routing.404')

    @http.route('/vem/eval/<int:evaluation_id>/save', type='json', auth='user', methods=['POST'])
    def save_evaluation_score(self, evaluation_id, **kwargs):
        """
        Saves or updates a single evaluation score.
        This function handles the saving of a score for a specific question
        and vendor in an evaluation. It performs rate limiting, validation,
        and access control checks before creating or updating the evaluation
        line.
        Args:
            evaluation_id (int): The ID of the evaluation.
            **kwargs: A dictionary containing the question_id, vendor_id, and
                      score.
        Returns:
            dict: A JSON response indicating the success or failure of the
                  operation, along with the updated vendor totals.
        """
        try:
            # Rate limiting check
            if not self._check_rate_limit(request.env.user.id):
                return {'success': False, 'error': 'Too many requests, please try again later'}

            # Get the evaluation record
            evaluation = request.env['vem.evaluation'].browse(evaluation_id)

            if not evaluation.exists():
                return {'success': False, 'error': 'Evaluation not found'}

            # Check if evaluation is in draft state
            if evaluation.state != 'draft':
                return {'success': False, 'error': 'Cannot modify evaluation in current state'}

            # Check access rights - use only check_access for Odoo 18
            evaluation.check_access('write')

            # Get request data
            question_id = kwargs.get('question_id')
            vendor_id = kwargs.get('vendor_id')
            score = kwargs.get('score')
            line_id = kwargs.get('line_id', 0)

            _logger.info(
                f"Saving score: evaluation_id={evaluation_id}, question_id={question_id}, vendor_id={vendor_id}, score={score}")

            # Validate input
            if not all([question_id, vendor_id]) or score is None:
                return {'success': False, 'error': 'Missing required parameters'}

            # Enhanced score validation
            try:
                score_int = int(score)
            except (ValueError, TypeError):
                return {'success': False, 'error': 'Score must be a valid integer'}

            if not (1 <= score_int <= 5):
                return {'success': False, 'error': 'Score must be between 1 and 5'}

            # Check if vendor is in evaluation
            if int(vendor_id) not in evaluation.vendor_ids.ids:
                return {'success': False, 'error': 'Vendor not in evaluation'}

            # Find or create evaluation line
            line_domain = [
                ('evaluation_id', '=', evaluation_id),
                ('question_id', '=', int(question_id)),
                ('vendor_id', '=', int(vendor_id))
            ]

            line = request.env['vem.evaluation.line'].search(line_domain, limit=1)

            if line:
                # Update existing line
                line.write({'score': int(score)})
                _logger.info(f"Updated existing line {line.id} with score {score}")
            else:
                # Create new line
                line = request.env['vem.evaluation.line'].create({
                    'evaluation_id': evaluation_id,
                    'question_id': int(question_id),
                    'vendor_id': int(vendor_id),
                    'score': int(score)
                })
                _logger.info(f"Created new line {line.id} with score {score}")

            # Recalculate vendor totals
            vendor_totals = {}
            for vendor in evaluation.vendor_ids:
                total = sum(evaluation.line_ids.filtered(
                    lambda l: l.vendor_id.id == vendor.id
                ).mapped('score'))
                vendor_totals[vendor.id] = total

            _logger.info(f"Vendor totals: {vendor_totals}")

            return {
                'success': True,
                'line_id': line.id,
                'vendor_totals': vendor_totals
            }

        except AccessError:
            return {'success': False, 'error': 'Access denied'}
        except Exception as e:
            _logger.error("Error saving evaluation score: %s", str(e))
            return {'success': False, 'error': f'Internal server error: {str(e)}'}

    @http.route('/vem/eval/<int:evaluation_id>/submit', type='json', auth='user', methods=['POST'])
    def submit_evaluation(self, evaluation_id, **kwargs):
        """
        Submits an evaluation for approval.
        This function changes the state of an evaluation from 'draft' to
        'submitted'. It performs access control checks to ensure that only
        authorized users can submit evaluations.
        Args:
            evaluation_id (int): The ID of the evaluation to submit.
            **kwargs: Additional keyword arguments.
        Returns:
            dict: A JSON response indicating the success or failure of the
                  operation.
        """
        try:
            # Get the evaluation record
            evaluation = request.env['vem.evaluation'].browse(evaluation_id)

            if not evaluation.exists():
                return {'success': False, 'error': 'Evaluation not found'}

            # Check if evaluation is in draft state
            if evaluation.state != 'draft':
                return {'success': False, 'error': 'Evaluation is not in draft state'}

            # Check access rights - use only check_access for Odoo 18
            evaluation.check_access('write')

            # Submit the evaluation (change state to submitted)
            evaluation.action_submit()

            return {'success': True, 'message': 'Evaluation submitted successfully'}

        except AccessError:
            return {'success': False, 'error': 'Access denied'}
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error("Error submitting evaluation: %s", str(e))
            return {'success': False, 'error': 'Internal server error'}

    @http.route('/vem/eval/<int:evaluation_id>/approve', type='json', auth='user', methods=['POST'])
    def approve_evaluation(self, evaluation_id, **kwargs):
        """
        Approves an evaluation.
        This function is restricted to users with the 'manager' role. It
        changes the state of an evaluation from 'submitted' to 'approved'.
        Access control checks are performed to ensure that only authorized
        managers can approve evaluations.
        Args:
            evaluation_id (int): The ID of the evaluation to approve.
            **kwargs: Additional keyword arguments.
        Returns:
            dict: A JSON response indicating the success or failure of the
                  operation.
        """
        try:
            # Check if user is manager
            if not request.env.user.has_group('tpm_score_summary.group_vem_manager'):
                return {'success': False, 'error': 'Only managers can approve evaluations'}

            # Get the evaluation record
            evaluation = request.env['vem.evaluation'].browse(evaluation_id)

            if not evaluation.exists():
                return {'success': False, 'error': 'Evaluation not found'}

            # Check access rights - use only check_access for Odoo 18
            evaluation.check_access('write')

            # Approve the evaluation
            evaluation.action_approve()

            return {'success': True}

        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except AccessError:
            return {'success': False, 'error': 'Access denied'}
        except Exception as e:
            _logger.error("Error approving evaluation: %s", str(e))
            return {'success': False, 'error': 'Internal server error'}

    @http.route('/vem/tpm_summary', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def tpm_evaluation_summary(self, **kwargs):
        """
        Displays a summary of multiple TPM evaluations.
        This function retrieves the summary data for a list of evaluations and
        renders a template to display the information. It performs access
        control checks to ensure that the user has the right to view the
        evaluations.
        Args:
            **kwargs: A dictionary containing the 'evaluation_ids' as a
                      comma-separated string.
        Returns:
            odoo.http.Response: The rendered summary template.
        """
        try:
            # Get evaluation IDs from POST data or GET parameters
            evaluation_ids = kwargs.get('evaluation_ids', '')
            if isinstance(evaluation_ids, str):
                evaluation_ids = [int(x) for x in evaluation_ids.split(',') if x.strip()]

            if not evaluation_ids:
                return request.render('http_routing.404')

            # Get evaluations
            evaluations = request.env['vem.evaluation'].browse(evaluation_ids)

            # Check if any evaluations exist
            if not evaluations.exists():
                return request.render('http_routing.404')

            # Check access rights
            try:
                evaluations.check_access('read')
            except AccessError:
                return request.render('http_routing.403')

            # Get multi-evaluation summary data
            summary_data = request.env['vem.evaluation'].get_multi_evaluation_summary(evaluation_ids)

            return request.render('tpm_score_summary.multi_summary_template', {
                'summary_data': summary_data,
                'evaluations': evaluations,
            })

        except Exception as e:
            _logger.error(f"Error rendering TPM evaluation summary: {str(e)}")
            return request.render('http_routing.404')
