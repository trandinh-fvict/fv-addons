# TPM Score Summary

This module provides a comprehensive system for evaluating vendors or teams based on a set of predefined questions. It allows for multiple evaluators to score multiple teams, and then generates a summary report of the results.

## Features

-   **Vendor Evaluation:** Evaluate multiple vendors or teams against a set of questions.
-   **Scoring Matrix:** A user-friendly interface for entering scores.
-   **Multi-Evaluation Summary:** Generate a summary report for multiple evaluations.
-   **Access Control:** Different levels of access for evaluators and managers.
-   **Rate Limiting:** Prevents abuse from rapid-fire requests.

## Installation

1.  Add the `tpm_score_summary` module to your Odoo addons path.
2.  Install the module in Odoo.

## Usage

1.  **Create an Evaluation:**
    -   Go to the "Vendor Evaluations" menu and create a new evaluation.
    -   Enter the evaluator's name and select the teams to be evaluated.
    -   Click the "Open Evaluation Matrix" button to open the scoring matrix.
2.  **Score the Teams:**
    -   In the scoring matrix, enter a score from 1 to 5 for each question and team.
    -   The scores are saved automatically as you enter them.
3.  **Submit the Evaluation:**
    -   Once all the scores have been entered, click the "Submit Evaluation" button.
4.  **View the Summary:**
    -   To view a summary of multiple evaluations, select the evaluations from the list view and click the "Summary Preview" button.

## Contributing

Contributions are welcome! If you have any suggestions or improvements, please create a pull request or an issue.

## License

This module is licensed under the OPL-1 license.