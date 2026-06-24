import json

class PitchGenerator:
    def __init__(self):
        pass

    def generate_pitch(self, combined_summary, filenames, topic_distribution_json):
        title_topic = "this research area"
        try:
            topics = json.loads(topic_distribution_json)
            if topics:
                title_topic = max(topics, key=topics.get)
        except Exception:
            pass

        paper_count = len(filenames) if filenames else 1
        papers_label = f"{paper_count} paper" if paper_count == 1 else f"{paper_count} papers"

        intro = f"A concise research pitch for {title_topic}."
        if combined_summary:
            intro = f"A concise pitch summarizing {papers_label} around {title_topic}."

        summary_preview = combined_summary.strip().replace("\n", " ")
        if len(summary_preview) > 230:
            summary_preview = summary_preview[:230].rstrip() + "..."

        pitch = (
            f"{intro} It identifies a core problem, highlights key contributions, "
            f"and points to a strong future direction. \n\n"
            f"Main insight: {summary_preview} \n\n"
            f"Elevator pitch: This work explores {title_topic}, identifies gaps in current approaches, "
            f"and proposes a focused research path with clear practical benefits and next-step experiments."
        )

        return pitch
