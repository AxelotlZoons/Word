
class Spotter:
    def __init__(self, keywords, keyword_thresholds, confidence_threshold=0.85):
        self.keywords = keywords
        self.threshold = confidence_threshold
        self.counts = {keyword: 0 for keyword in self.keywords}
        self.seen_in_sentence = set()

    def spot(self, data):
        # Reset when final arrives
        if data.get("is_final"):
            self.seen_in_sentence.clear()

        if "channel" not in data:
            return []

        alternatives = data["channel"]["alternatives"]
        if not alternatives:
            return []

        words = alternatives[0].get("words", [])
        matches = []

        for word in words:
            text = word["word"]
            confidence = word["confidence"]
            word_id = (text, word["start"])
            if word_id not in self.seen_in_utterance:
                self.seen_in_utterance.add(word_id)
                self.counts[text] += 1
                matches.append(text)

        return matches