import re

def clean_think_tags(text: str) -> str:
    if not text:
        return ""
    # Strip complete <think>...</think> and <vthink>...</vthink> blocks (case-insensitive, multi-line)
    text = re.sub(r'<(v?think)>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Strip unclosed <think> or <vthink> blocks (remove from the tag to the end of the text)
    text = re.sub(r'<(v?think)>.*$', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Strip any stray closing tags
    text = re.sub(r'</(v?think)>', '', text, flags=re.IGNORECASE)
    return text.strip()

sample = "<think>huh, seems like a pretty casual convo so far, wonder what they're up to</think> heyy..."
print("Result:", clean_think_tags(sample))
