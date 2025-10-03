/** @odoo-module **/

// Evaluation Matrix functionality for vendor evaluation
let saveQueue = [];
let isProcessingQueue = false;
let debounceTimers = {};
let lastSaveTime = {}; // Track last save time for each input
let pendingChanges = {}; // Track pending changes that haven't been processed

// Add rate limiting and concurrency control
const RATE_LIMIT_WINDOW = 2000; // 2 seconds window
const MAX_REQUESTS_PER_WINDOW = 5; // Maximum 5 requests per window
const requestCounts = new Map();

$(document).ready(function() {
    // Wait for DOM to be fully loaded
    setTimeout(function() {
        initializeEvaluationMatrix();
    }, 100);
});
/**
 * Initializes the evaluation matrix functionality.
 * This function sets up event handlers for score inputs and the submit button
 * on the evaluation matrix page. It uses debouncing to prevent excessive
 * server requests when a user is typing in scores.
 */
function initializeEvaluationMatrix() {
    const $matrix = $('#evaluation_matrix');

    if ($matrix.length === 0) {
        return; // Not on evaluation matrix page
    }

    const evaluationId = parseInt($matrix.data('evaluation-id'));

    if (!evaluationId) {
        console.error('Evaluation ID not found');
        return;
    }

    // Check if already initialized
    if ($matrix.data('initialized')) {
        return;
    }

    // Mark as initialized
    $matrix.data('initialized', true);

    // Initialize score change handlers with longer debouncing
    $(document).off('input.matrix change.matrix', '.score-input').on('input.matrix change.matrix', '.score-input', function(event) {
        const $input = $(event.currentTarget);
        const inputId = $input.data('question-id') + '_' + $input.data('vendor-id');

        // Clear existing timer for this input
        if (debounceTimers[inputId]) {
            clearTimeout(debounceTimers[inputId]);
        }

        // Store the pending change
        pendingChanges[inputId] = {
            $input: $input,
            value: $input.val(),
            timestamp: Date.now()
        };

        // Set new timer with 1000ms delay (increased from 300ms)
        debounceTimers[inputId] = setTimeout(function() {
            // Only process if this is still the latest change
            if (pendingChanges[inputId] && pendingChanges[inputId].value === $input.val()) {
                validateAndHandleScoreChange($input, evaluationId);
                delete pendingChanges[inputId];
            }
            delete debounceTimers[inputId];
        }, 1000);
    });

    // Initialize submit button handler
    $(document).off('click.matrix', '#submit_evaluation').on('click.matrix', '#submit_evaluation', function(event) {
        handleSubmitEvaluation($(event.currentTarget), evaluationId);
    });
}
/**
 * Validates a score to ensure it is a whole number between 1 and 5.
 * @param {string} score - The score to validate.
 * @returns {object} An object with a 'valid' boolean and a 'message' string
 *                   if the score is invalid.
 */
function validateScore(score) {
    const numScore = parseFloat(score);

    // Check if it's a valid number
    if (isNaN(numScore)) {
        return { valid: false, message: 'Please enter a valid number' };
    }

    // Check if it's an integer
    if (!Number.isInteger(numScore)) {
        return { valid: false, message: 'Score must be a whole number (1, 2, 3, 4, or 5)' };
    }

    // Check if it's in valid range
    if (numScore < 1 || numScore > 5) {
        return { valid: false, message: 'Score must be between 1 and 5' };
    }

    return { valid: true, score: numScore };
}
/**
 * Checks if a request should be rate-limited.
 * This function implements a simple rate limiting mechanism to prevent
 * excessive server requests from a single input field.
 * @param {string} inputId - The ID of the input field to check.
 * @returns {boolean} True if the request should be rate-limited, false
 *                    otherwise.
 */
function isRateLimited(inputId) {
    const now = Date.now();
    const windowStart = now - RATE_LIMIT_WINDOW;

    // Clean up old entries
    for (const [key, data] of requestCounts) {
        if (data.timestamp < windowStart) {
            requestCounts.delete(key);
        }
    }

    // Get or initialize request count for this input
    const data = requestCounts.get(inputId) || { count: 0, timestamp: now };

    if (data.timestamp < windowStart) {
        data.count = 1;
        data.timestamp = now;
    } else if (data.count >= MAX_REQUESTS_PER_WINDOW) {
        return true;
    } else {
        data.count++;
    }

    requestCounts.set(inputId, data);
    return false;
}

/**
 * Validates a score input and handles the change.
 * This function is called when a score input changes. It validates the new
 * score, and if it is valid, it either saves the score immediately or queues
 * it for later if the rate limit has been exceeded.
 * @param {jQuery} $input - The jQuery object for the score input.
 * @param {number} evaluationId - The ID of the evaluation.
 */
function validateAndHandleScoreChange($input, evaluationId) {
    const inputValue = $input.val().trim();
    const inputId = $input.data('question-id') + '_' + $input.data('vendor-id');

    // Clear previous validation states
    $input.removeClass('success error invalid');

    if (inputValue === '') return;

    const validation = validateScore(inputValue);
    if (!validation.valid) {
        $input.addClass('invalid');
        // Show validation message without blocking
        $input.closest('.score-cell').find('.validation-message').text(validation.message);
        return;
    }

    // Optimistic UI update
    $input.addClass('pending');

    // Check rate limiting
    if (isRateLimited(inputId)) {
        console.log('Rate limited, queuing update');
        queueScoreUpdate($input, evaluationId, validation.score);
        return;
    }

    saveScore($input, evaluationId, validation.score);
}
/**
 * Queues a score update to be processed later.
 * This function is used when the rate limit has been exceeded. It adds the
 * score update to a queue, which is processed asynchronously.
 * @param {jQuery} $input - The jQuery object for the score input.
 * @param {number} evaluationId - The ID of the evaluation.
 * @param {number} score - The score to be saved.
 */
function queueScoreUpdate($input, evaluationId, score) {
    const updateData = {
        $input,
        evaluationId,
        score,
        timestamp: Date.now()
    };

    saveQueue.push(updateData);

    if (!isProcessingQueue) {
        processQueue();
    }
}
/**
 * Processes the queue of score updates.
 * This function is called asynchronously to process the score updates that
 * have been queued due to rate limiting. It processes one update at a time
 * and then schedules itself to run again after a delay.
 */
function processQueue() {
    if (saveQueue.length === 0) {
        isProcessingQueue = false;
        return;
    }

    isProcessingQueue = true;
    const update = saveQueue[0];

    if (!isRateLimited(update.$input.data('question-id') + '_' + update.$input.data('vendor-id'))) {
        saveQueue.shift();
        saveScore(update.$input, update.evaluationId, update.score);
    }

    // Process next item in queue after delay
    setTimeout(processQueue, 500);
}

/**
 * Saves a score to the server using an AJAX request.
 * This function sends the score to the server to be saved. It includes retry
 * logic with exponential backoff to handle network errors.
 * @param {jQuery} $input - The jQuery object for the score input.
 * @param {number} evaluationId - The ID of the evaluation.
 * @param {number} score - The score to be saved.
 * @returns {Promise} A promise that resolves when the score is saved
 *                    successfully.
 */
function saveScore($input, evaluationId, score) {
    const questionId = $input.data('question-id');
    const vendorId = $input.data('vendor-id');

    // Optimistic UI feedback
    $input.addClass('saving').removeClass('error success');

    // Add session token to prevent CSRF issues
    const session_info = odoo.session_info || {};
    const csrf_token = session_info.csrf_token;

    function attemptSave() {
        return $.ajax({
            url: '/web/dataset/call_kw/vem.evaluation/save_score',
            type: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            data: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    model: 'vem.evaluation',
                    method: 'save_score',
                    args: [evaluationId, questionId, vendorId, score],
                    kwargs: {}
                },
                id: Math.floor(Math.random() * 1000000000)
            }),
            success: function(response) {
                if (response.error) {
                    throw new Error(response.error.data.message || 'Server error occurred');
                }
                $input.removeClass('saving pending').addClass('success');
                setTimeout(() => $input.removeClass('success'), 2000);
            },
            error: function(xhr, status, error) {
                console.error('Save failed:', {
                    status: xhr.status,
                    statusText: xhr.statusText,
                    responseText: xhr.responseText,
                    error: error
                });
                throw new Error(error || 'Network error');
            }
        });
    }

    // Implementation with better error handling and retry logic
    let retryCount = 0;
    const maxRetries = 3;
    const backoffDelay = 1000; // Start with 1 second

    function tryWithRetry() {
        return attemptSave().catch(function(error) {
            retryCount++;
            if (retryCount < maxRetries) {
                console.log(`Retry attempt ${retryCount} after error:`, error);
                // Exponential backoff
                const delay = backoffDelay * Math.pow(2, retryCount - 1);
                return new Promise(resolve => setTimeout(resolve, delay))
                    .then(tryWithRetry);
            } else {
                $input.removeClass('saving pending').addClass('error');
                console.error('Failed to save score after ' + maxRetries + ' attempts:', error);
                // Show error message to user
                const errorMessage = $('<div>')
                    .addClass('save-error-message')
                    .text('Failed to save. Please try again.')
                    .insertAfter($input);
                setTimeout(() => errorMessage.fadeOut('slow', function() { $(this).remove(); }), 5000);
                throw error;
            }
        });
    }

    return tryWithRetry();
}
/**
 * Validates all scores on the page.
 * This function iterates through all score inputs and validates them. It
 * returns an object indicating whether all scores are valid and a list of
 * any invalid inputs.
 * @returns {object} An object with a 'valid' boolean and a list of
 *                   'invalidInputs'.
 */
function validateAllScores() {
    let hasInvalidScores = false;
    const invalidInputs = [];

    $('.score-input').each(function() {
        const $input = $(this);
        const value = $input.val().trim();

        if (value) {
            const validation = validateScore(value);
            if (!validation.valid) {
                hasInvalidScores = true;
                invalidInputs.push({
                    element: $input,
                    message: validation.message
                });
                $input.addClass('invalid');
            } else {
                $input.removeClass('invalid');
            }
        }
    });

    return { valid: !hasInvalidScores, invalidInputs: invalidInputs };
}
/**
 * Handles the submission of an evaluation.
 * This function is called when the user clicks the submit button. It validates
 * all scores, asks for confirmation, and then sends an AJAX request to submit
 * the evaluation.
 * @param {jQuery} $button - The jQuery object for the submit button.
 * @param {number} evaluationId - The ID of the evaluation.
 */
function handleSubmitEvaluation($button, evaluationId) {
    if (!evaluationId) {
        alert('Error: Evaluation ID not found');
        return;
    }

    // Wait for any pending saves to complete
    if (saveQueue.length > 0 || isProcessingQueue) {
        alert('Please wait for all scores to be saved before submitting...');

        // Check again after 2 seconds
        setTimeout(function() {
            if (saveQueue.length === 0 && !isProcessingQueue) {
                handleSubmitEvaluation($button, evaluationId);
            }
        }, 2000);
        return;
    }

    // Validate all scores before submit
    const scoreValidation = validateAllScores();

    if (!scoreValidation.valid) {
        let errorMessage = 'Please fix the following errors before submitting:\n\n';
        scoreValidation.invalidInputs.forEach(function(item, index) {
            errorMessage += (index + 1) + '. ' + item.message + '\n';
        });
        errorMessage += '\nAll scores must be whole numbers between 1 and 5.';

        alert(errorMessage);

        // Focus on first invalid input
        if (scoreValidation.invalidInputs.length > 0) {
            scoreValidation.invalidInputs[0].element.focus();
        }

        return;
    }

    if (!confirm('Are you sure you want to submit this evaluation? You will not be able to modify it afterwards.')) {
        return;
    }

    // Update button state
    $button.prop('disabled', true).text('Submitting...');

    // Send submit request
    $.ajax({
        url: '/vem/eval/' + evaluationId + '/submit',
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        timeout: 15000, // 15 second timeout for submit
        data: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {}
        }),
        success: function(response) {
            if (response.result && response.result.success) {
                alert('Evaluation submitted successfully!');
                location.reload();
            } else {
                alert('Error submitting evaluation: ' + (response.result ? response.result.error : 'Unknown error'));
                $button.prop('disabled', false).text('Submit Evaluation');
            }
        },
        error: function(xhr, status, error) {
            console.error('Submit request failed:', error);
            alert('Error submitting evaluation: ' + error);
            $button.prop('disabled', false).text('Submit Evaluation');
        }
    });
}
