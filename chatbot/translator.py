"""Translation Service Module
Handles multi-language support for the chatbot
"""

class TranslationService:
    """Handles translation between supported languages"""

    SUPPORTED_LANGUAGES = {
        'english': 'en',
        'chinese': 'zh-CN',
        'mandarin': 'zh-CN',
        'french': 'fr'
    }

    def __init__(self):
        self.current_language = 'en'
        self.translator_available = False
        self._initialize_translator()

    def _initialize_translator(self):
        """Initialize the translation library"""
        try:
            from deep_translator import GoogleTranslator
            self.translator_available = True
        except ImportError:
            print("Warning: deep-translator not installed. Translation disabled.")
            print("Install with: pip install deep-translator")
            self.translator_available = False

    def set_language(self, language):
        """
        Set the current language

        Args:
            language: Language name (english, chinese, french)

        Returns:
            bool: True if language was set successfully
        """
        language_lower = language.lower()
        if language_lower in self.SUPPORTED_LANGUAGES:
            self.current_language = self.SUPPORTED_LANGUAGES[language_lower]
            return True
        return False

    def get_current_language_name(self):
        """Get the human-readable name of current language"""
        lang_names = {
            'en': 'English',
            'zh-CN': 'Chinese (Mandarin)',
            'fr': 'French'
        }
        return lang_names.get(self.current_language, 'English')

    def translate(self, text):
        """
        Translate text to current language

        Args:
            text: Text to translate

        Returns:
            str: Translated text, or original if translation fails
        """
        # If English or translation disabled, return as-is
        if self.current_language == 'en' or not self.translator_available:
            return text

        try:
            from deep_translator import GoogleTranslator

            # Translate to target language
            translator = GoogleTranslator(source='en', target=self.current_language)
            result = translator.translate(text)
            return result
        except Exception as e:
            # If translation fails, return original text
            print(f"Translation error: {e}")
            return text

    def get_language_menu(self):
        """Get the language selection menu"""
        if self.current_language == 'en':
            return (
                "Choose your language / 选择语言 / Choisissez votre langue:\n"
                "  1. English\n"
                "  2. 中文 (Chinese - Mandarin)\n"
                "  3. Français (French)\n\n"
                "Type: 'language english' or 'language chinese' or 'language french'"
            )
        else:
            # Show menu in current language
            menu = (
                "Choose your language / 选择语言 / Choisissez votre langue:\n"
                "  1. English\n"
                "  2. 中文 (Chinese - Mandarin)\n"
                "  3. Français (French)\n\n"
                "Type: 'language english' or 'language chinese' or 'language french'"
            )
            return menu
