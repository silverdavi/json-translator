import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import numpy as np

class ValidationVisualizer:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.reports_dir = os.path.join(output_dir, "reports")
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_report_dir = os.path.join(self.reports_dir, f"report_{self.run_id}")
        os.makedirs(self.current_report_dir, exist_ok=True)

    def _load_validation_data(self, validation_file: str) -> Dict:
        with open(validation_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _create_score_histogram(self, scores: List[float], title: str, filename: str):
        plt.figure(figsize=(10, 6))
        sns.histplot(scores, bins=20)
        plt.title(title)
        plt.xlabel('Score')
        plt.ylabel('Count')
        plt.savefig(os.path.join(self.current_report_dir, filename))
        plt.close()

    def _create_category_radar(self, data: Dict[str, float], title: str, filename: str):
        # Get category names and values
        categories = list(data.keys())
        values = list(data.values())
        
        # Number of variables
        num_vars = len(categories)
        
        # Compute angle for each axis
        angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
        angles += angles[:1]  # Complete the circle
        
        # Initialize the spider plot
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # Plot data
        values = values + [values[0]]  # Complete the circle
        ax.plot(angles, values)
        ax.fill(angles, values, alpha=0.25)
        
        # Fix axis to go in the right order and start at 12 o'clock
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        
        # Add title
        plt.title(title)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.current_report_dir, filename))
        plt.close()

    def _create_low_score_examples(self, validation_data: Dict, filename: str):
        low_scores = [item for item in validation_data['quality_details']['sentence_scores'] 
                     if item['score'] < 90]
        
        if not low_scores:
            return
        
        with open(os.path.join(self.current_report_dir, filename), 'w', encoding='utf-8') as f:
            f.write("# Low Score Examples\n\n")
            for item in low_scores:
                f.write(f"## {item['path']}\n")
                f.write(f"- Original: {item['original']}\n")
                f.write(f"- Translation: {item['translation']}\n")
                f.write(f"- Score: {item['score']}\n")
                f.write(f"- Comments: {item['comments']}\n\n")

    def _get_examples_by_score_group(self, df_scores: pd.DataFrame) -> Dict[str, List]:
        """Get examples of translations from different score groups."""
        # Define score groups
        score_groups = {
            "Perfect (100)": df_scores[df_scores['score'] == 100],
            "Excellent (95-99)": df_scores[(df_scores['score'] >= 95) & (df_scores['score'] < 100)],
            "Good (90-94)": df_scores[(df_scores['score'] >= 90) & (df_scores['score'] < 95)],
            "Fair (80-89)": df_scores[(df_scores['score'] >= 80) & (df_scores['score'] < 90)],
            "Poor (<80)": df_scores[df_scores['score'] < 80]
        }
        
        # Get one example from each group if available
        examples = {}
        for group_name, group_df in score_groups.items():
            if not group_df.empty:
                # Take the first example from each group
                examples[group_name] = group_df.iloc[0].to_dict()
        
        return examples

    def generate_report(self, validation_files: List[str], language: str = None):
        """Generate comprehensive visualization report for validation results."""
        
        # Create summary DataFrame
        all_scores = []
        all_categories = []
        
        for file in validation_files:
            data = self._load_validation_data(file)
            filename = os.path.basename(file)
            
            # Add sentence scores
            for score in data['quality_details']['sentence_scores']:
                score['file'] = filename
                all_scores.append(score)
            
            # Add category scores
            categories = data['quality_details']['categories'].copy()
            categories['file'] = filename
            all_categories.append(categories)
        
        df_scores = pd.DataFrame(all_scores)
        df_categories = pd.DataFrame(all_categories)
        
        # Generate visualizations
        self._create_score_histogram(
            df_scores['score'].values,
            f"Score Distribution {'for ' + language if language else ''}",
            "score_distribution.png"
        )
        
        if language:
            # Calculate mean category scores excluding the 'file' column
            category_means = df_categories.drop('file', axis=1).mean().to_dict()
            self._create_category_radar(
                category_means,
                f"Category Scores for {language}",
                f"category_radar_{language}.png"
            )
        
        # Generate low score examples
        self._create_low_score_examples(
            self._load_validation_data(validation_files[0]),
            "low_score_examples.md"
        )
        
        # Get examples by score group
        score_examples = self._get_examples_by_score_group(df_scores)
        
        # Generate summary report
        with open(os.path.join(self.current_report_dir, "summary.md"), 'w', encoding='utf-8') as f:
            f.write("# Translation Validation Summary\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if language:
                f.write(f"## Language: {language}\n\n")
            
            # Add detailed statistics
            f.write("## Translation Statistics\n")
            f.write(f"- Total strings translated: {len(df_scores)}\n")
            f.write(f"- Number of files processed: {len(validation_files)}\n")
            
            # Score distribution statistics
            score_counts = df_scores['score'].value_counts().sort_index(ascending=False)
            f.write(f"- Perfect scores (100): {score_counts.get(100, 0)} strings ({score_counts.get(100, 0)/len(df_scores)*100:.1f}%)\n")
            f.write(f"- Excellent scores (95-99): {sum((df_scores['score'] >= 95) & (df_scores['score'] < 100))} strings ({sum((df_scores['score'] >= 95) & (df_scores['score'] < 100))/len(df_scores)*100:.1f}%)\n")
            f.write(f"- Good scores (90-94): {sum((df_scores['score'] >= 90) & (df_scores['score'] < 95))} strings ({sum((df_scores['score'] >= 90) & (df_scores['score'] < 95))/len(df_scores)*100:.1f}%)\n")
            f.write(f"- Fair scores (80-89): {sum((df_scores['score'] >= 80) & (df_scores['score'] < 90))} strings ({sum((df_scores['score'] >= 80) & (df_scores['score'] < 90))/len(df_scores)*100:.1f}%)\n")
            f.write(f"- Poor scores (<80): {sum(df_scores['score'] < 80)} strings ({sum(df_scores['score'] < 80)/len(df_scores)*100:.1f}%)\n\n")
            
            f.write("## Overall Statistics\n")
            f.write(f"- Average Score: {df_scores['score'].mean():.2f}\n")
            f.write(f"- Median Score: {df_scores['score'].median():.2f}\n")
            f.write(f"- Standard Deviation: {df_scores['score'].std():.2f}\n")
            f.write(f"- Minimum Score: {df_scores['score'].min():.2f}\n")
            f.write(f"- Maximum Score: {df_scores['score'].max():.2f}\n\n")
            
            f.write("## Category Averages\n")
            category_means = df_categories.drop('file', axis=1).mean()
            for category, value in category_means.items():
                f.write(f"- {category}: {value:.2f}\n")
            
            f.write("\n## Files Processed\n")
            for file in validation_files:
                base_filename = os.path.basename(file)
                file_data = self._load_validation_data(file)
                num_strings = len(file_data['quality_details']['sentence_scores'])
                avg_score = sum(item['score'] for item in file_data['quality_details']['sentence_scores']) / num_strings
                f.write(f"- {base_filename} ({num_strings} strings, avg score: {avg_score:.2f})\n")
            
            # Add examples from each score group
            f.write("\n## Translation Examples by Score Group\n")
            if score_examples:
                for group_name, example in score_examples.items():
                    f.write(f"\n### {group_name}\n")
                    f.write(f"- **Key**: `{example['path']}`\n")
                    f.write(f"- **Original**: {example['original']}\n")
                    f.write(f"- **Translation**: {example['translation']}\n")
                    f.write(f"- **Score**: {example['score']}\n")
            else:
                f.write("\nNo examples available.\n")
                
            # File-specific statistics
            f.write("\n## Per-File Statistics\n")
            for file in validation_files:
                base_filename = os.path.basename(file)
                file_data = self._load_validation_data(file)
                f.write(f"\n### {base_filename}\n")
                f.write(f"- Structure Score: {file_data['structure_score']:.2f}\n")
                f.write(f"- Quality Score: {file_data['quality_score']:.2f}\n")
                
                # Count score distribution within this file
                file_scores = [item['score'] for item in file_data['quality_details']['sentence_scores']]
                perfect = sum(1 for s in file_scores if s == 100)
                excellent = sum(1 for s in file_scores if 95 <= s < 100)
                good = sum(1 for s in file_scores if 90 <= s < 95)
                fair = sum(1 for s in file_scores if 80 <= s < 90)
                poor = sum(1 for s in file_scores if s < 80)
                
                f.write("- Score distribution:\n")
                f.write(f"  - Perfect (100): {perfect} ({perfect/len(file_scores)*100:.1f}%)\n")
                f.write(f"  - Excellent (95-99): {excellent} ({excellent/len(file_scores)*100:.1f}%)\n")
                f.write(f"  - Good (90-94): {good} ({good/len(file_scores)*100:.1f}%)\n")
                f.write(f"  - Fair (80-89): {fair} ({fair/len(file_scores)*100:.1f}%)\n")
                f.write(f"  - Poor (<80): {poor} ({poor/len(file_scores)*100:.1f}%)\n") 