
import inflect


class Spotter:
    def __init__(self, keywords, confidence_threshold=0.85):
        self.keywords = keywords
        self.inflector = inflect.engine()
        self._map_keywords_inflection()
        self.threshold = confidence_threshold
        self.keyword_counts = {keyword: 0 for keyword in self.keywords}
        self.keyword_counts_path = "keyword_counts.txt"
        self._clear_keyword_counts()
        self._render_keyword_counts()


    def _map_keywords_inflection(self):
        self.keywords_inflection_mapping = {}

        for keyword in self.keywords:
            plural = self.inflector.plural(keyword)
            singular_poss = f"{keyword}'s"
            plural_poss = f"{plural}'" if plural.endswith("s") else f"{plural}'s"

            self.keywords_inflection_mapping[keyword] = keyword
            self.keywords_inflection_mapping[plural] = keyword
            self.keywords_inflection_mapping[singular_poss] = keyword
            self.keywords_inflection_mapping[plural_poss] = keyword


    def spot(self, transcript):

        if "channel" not in transcript:
            return

        alternatives = transcript["channel"]["alternatives"]
        if not alternatives:
            return

        words = alternatives[0].get("words", [])

        for word in words:
            text = word["word"]
            confidence = word["confidence"]
 
            if text in self.keywords_inflection_mapping and confidence >= self.threshold:
                root_keyword = self.keywords_inflection_mapping[text]
                print(f"[SPOTTER] {root_keyword} at {round(word["start"], 0)}")
                self.keyword_counts[root_keyword] += 1
                self._render_keyword_counts()


    def _clear_keyword_counts(self):
        with open(self.keyword_counts_path, "a") as f:
            f.truncate(0)


    def _render_keyword_counts(self):
        line = " | ".join(f"{k}:{v}" for k, v in sorted(self.keyword_counts.items()))
        with open(self.keyword_counts_path, "a") as f:
            f.write(line + "\n")
