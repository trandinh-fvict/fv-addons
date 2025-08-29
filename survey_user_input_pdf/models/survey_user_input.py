from odoo import models, api
import json


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    # def _get_pdf_command(self):
    #     """Override to add custom wkhtmltopdf arguments."""
    #     command = super()._get_pdf_command()
    #     command.extend([
    #         '--page-size', '',
    #         '--disable-smart-shrinking',
    #         '--no-stop-slow-scripts',
    #         '--enable-local-file-access',
    #         '--javascript-delay', '1000',
    #         '--margin-top', '10',
    #         '--margin-bottom', '5',
    #         '--margin-left', '3',
    #         '--margin-right', '3',
    #         '--page-width', '0',
    #         '--page-height', '0'
    #     ])
    #     return command

    def print_survey_user_input_pdf(self):
        """Print the survey response as PDF with custom options."""
        self.ensure_one()
        report_action = self.env.ref('survey_user_input_pdf.action_report_survey_user_input_pdf')

        # Update paperformat settings
        report_action.paperformat_id.write({
            'format': 'custom',
            'page_height': 0,
            'page_width': 0,
            'margin_top': 10,
            'margin_bottom': 5,
            'margin_left': 3,
            'margin_right': 3,
            'header_spacing': 0,
            'dpi': 96
        })

        # Customize PDF generation context
        pdf_context = {
            'disable_internal_links': True,
            'disable_external_links': True,
            'force_report_rendering': True,
            'wkhtmltopdf_flags': {
                '--page-size': '',
                '--disable-smart-shrinking': '',
                '--viewport-size': '',
                '--no-stop-slow-scripts': '',
                '--javascript-delay': '1000',
                '--enable-local-file-access': '',
                '--margin-top': '10',
                '--margin-bottom': '5',
                '--margin-left': '3',
                '--margin-right': '3',
                '--page-width': '0',
                '--page-height': '0'
            }
        }

        return report_action.with_context(**pdf_context).report_action(self)

    def _render_qweb_pdf(self, report_ref, data=None):
        """Override to customize PDF rendering process."""
        # Get the report
        report = self.env['ir.actions.report']._get_report(report_ref)

        # Update context
        self = self.with_context(
            report_pdf=True,
            disable_page_breaks=True,
            force_report_rendering=True
        )

        return super()._render_qweb_pdf(report_ref, data)

    def action_preview_survey_user_input_pdf(self):
        """Preview the survey response as html in browser."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_action = self.env.ref('survey_user_input_pdf.action_report_survey_user_input_pdf')

        if len(self) > 1:
            # Multiple records - combine IDs
            ids = ','.join(map(str, self.ids))
            url = f'{base_url}/report/html/{report_action.report_name}/{ids}'
        else:
            # Single record
            url = f'{base_url}/report/html/{report_action.report_name}/{self.id}'

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
