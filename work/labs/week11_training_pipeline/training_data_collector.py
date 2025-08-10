# D:\python_workspace\project_nlp\iSpan_LLM-Agent-cookbooks\work\labs\week11_training_pipeline\training_data_collector.py
import json
from typing import List, Dict, Any

class TrainingDataCollector:
    """A class to collect and save training data in JSONL format."""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.training_data: List[Dict[str, Any]] = []

    def collect(self, original_prompt: str, refined_content: str):
        """Collects a single data point."""
        data_point = {
            "prompt": original_prompt,
            "completion": refined_content
        }
        self.training_data.append(data_point)
        print(f"Data point collected. Total points: {len(self.training_data)}")

    def save(self):
        """Saves the collected data to a JSONL file."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for entry in self.training_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"Successfully saved {len(self.training_data)} data points to {self.output_file}")
