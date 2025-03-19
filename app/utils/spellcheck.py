from spellchecker import SpellChecker

def correct_text(text):
    spell = SpellChecker()
    # Tokenize text into words (this is a simple split; you might use a more advanced tokenizer)
    words = text.split()
    # Find misspelled words
    misspelled = spell.unknown(words)
    corrected_words = []
    for word in words:
        if word in misspelled:
            corrected = spell.correction(word)
            corrected_words.append(corrected)
        else:
            corrected_words.append(word)
    return ' '.join(corrected_words)
