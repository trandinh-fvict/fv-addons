# # -*- coding: utf-8 -*-
# import google.generativeai as genai
# import logging
# from odoo import http, _
# from odoo.http import request
# from odoo.addons.html_editor.controllers.main import HTML_Editor
#
# _logger = logging.getLogger(__name__)
#
#
# class GeminiConnectorController(HTML_Editor):
#
#     @http.route('/web_editor/generate_text', type='json', auth='user')
#     @http.route('/html_editor/generate_text', type='json', auth='user')
#     def generate_text(self, prompt, conversation_history):
#         config = request.env['ir.config_parameter'].sudo()
#         gemini_api_key = config.get_param('web_editor.gemini_api_key')
#         if gemini_api_key:
#             try:
#                 gemini_model_name = config.get_param('web_editor.gemini_model', 'gemini-2.5-flash')
#                 genai.configure(api_key=gemini_api_key)
#                 model = genai.GenerativeModel(gemini_model_name)
#                 response = model.generate_content(prompt)
#                 _logger.info("Successfully generated text with Google Gemini.")
#                 # Trả về duy nhất chuỗi văn bản. Odoo sẽ tự xử lý phần còn lại.
#                 return response.text.strip()
#             except Exception as e:
#                 _logger.warning("Gemini API call failed: %s. Falling back to default Odoo IAP service.", e)
#         _logger.info("Back to default Odoo IAP service for AI generation.")
#         return super(GeminiConnectorController, self).generate_text(prompt, conversation_history)

# -*- coding: utf-8 -*-
from google import genai
from google.genai import types
import logging
import time
import random
from odoo import http, _
from odoo.http import request
from odoo.addons.html_editor.controllers.main import HTML_Editor

_logger = logging.getLogger(__name__)


# --- Lớp quản lý API Key (Không thay đổi) ---
class GeminiApiKeyManager:
    def __init__(self, api_keys=None):
        if api_keys is None:
            api_keys = []
        self._all_keys = set(api_keys)
        self._good_keys = list(self._all_keys)
        self._bad_keys = {}
        self.cooldown_period = 600

    def _revive_keys(self):
        now = time.time()
        revived_keys = [key for key, failed_time in self._bad_keys.items() if now - failed_time > self.cooldown_period]
        for key in revived_keys:
            del self._bad_keys[key]
            if key in self._all_keys and key not in self._good_keys:
                self._good_keys.append(key)

    def get_key(self):
        self._revive_keys()
        if not self._good_keys:
            return None
        return random.choice(self._good_keys)

    def report_failure(self, key):
        if key in self._good_keys:
            self._good_keys.remove(key)
        self._bad_keys[key] = time.time()

    def update_keys(self, new_api_keys):
        self._all_keys = set(new_api_keys)
        current_bad_keys = set(self._bad_keys.keys())
        self._good_keys = list(self._all_keys - current_bad_keys)


# --- Biến toàn cục cho mỗi worker (Không thay đổi) ---
key_manager = None
last_config_check_time = 0
CONFIG_CHECK_INTERVAL = 300


def get_key_manager(env):
    global key_manager, last_config_check_time
    now = time.time()
    if not key_manager or now - last_config_check_time > CONFIG_CHECK_INTERVAL:
        _logger.info("Initializing or reloading Gemini API Key Manager...")
        config = env['ir.config_parameter'].sudo()
        gemini_api_keys_str = config.get_param('web_editor.gemini_api_key', '')
        api_keys = [key.strip() for key in gemini_api_keys_str.split(',') if key.strip()]
        if not key_manager:
            key_manager = GeminiApiKeyManager(api_keys)
        else:
            key_manager.update_keys(api_keys)
        last_config_check_time = now
        _logger.info("Key Manager loaded with %d total keys. %d good keys available.", len(key_manager._all_keys),
                     len(key_manager._good_keys))
    return key_manager


class GeminiConnectorController(HTML_Editor):

    @http.route('/web_editor/generate_text', type='json', auth='user')
    @http.route('/html_editor/generate_text', type='json', auth='user')
    def generate_text(self, prompt, conversation_history):
        manager = get_key_manager(request.env)
        config_sudo = request.env['ir.config_parameter'].sudo()
        gemini_model_name = config_sudo.get_param('web_editor.gemini_model', 'gemini-2.5-flash')
        enable_search = config_sudo.get_param('web_editor.gemini_enable_search_grounding', 'false').lower() in ('true',
                                                                                                                '1',
                                                                                                                't')

        max_retries = 5
        for i in range(max_retries):
            api_key = manager.get_key()
            if not api_key:
                _logger.warning("No available Gemini API keys in the manager pool.")
                break
            try:
                _logger.info("Attempt #%s: Using correct API structure.", i + 1)

                client = genai.Client(api_key=api_key)

                generation_params = {
                    'model': f'models/{gemini_model_name}',
                    'contents': prompt,
                }

                if enable_search:
                    _logger.info("Google Search grounding is enabled for this request.")
                    grounding_tool = types.Tool(
                        google_search=types.GoogleSearch()
                    )
                    # Sửa lại tên từ 'generation_config' thành 'config'
                    config_obj = types.GenerateContentConfig(
                        tools=[grounding_tool]
                    )
                    generation_params['config'] = config_obj

                response = client.models.generate_content(**generation_params)

                _logger.info("Successfully generated text with Google Gemini.")
                return response.text.strip()
            except Exception as e:
                _logger.warning(
                    "Gemini API call failed for a key. Reporting failure to manager. Error: %r", e
                )
                manager.report_failure(api_key)

        _logger.info("All Gemini attempts failed. Falling back to default Odoo IAP service.")
        return super(GeminiConnectorController, self).generate_text(prompt, conversation_history)
