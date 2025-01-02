import tkinter as tk
from tkinter import messagebox, ttk
from collections import Counter
import json
import os
import numpy as np
from datetime import datetime

class CardTableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Card Results Table")
        self.setup_variables()
        self.create_ui()
        self.load_data()
        self.setup_statistics()

    def setup_variables(self):
        self.colors = {"P": "#1E88E5", "B": "#E53935", "T": "#43A047"}
        self.cell_size = 50
        self.padding = 5
        self.rows = 6
        self.data_file = "results.json"
        self.ml_file = "ml_data.json"
        self.results = []
        self.ml_data = []
        self.patterns = []
        self.display_count = 30
        self.timestamps = []
        self.current_prediction = None
        self.prediction_stats = {
            'correct': 0,
            'incorrect': 0,
            'total': 0
        }

    def setup_statistics(self):
        self.stats = {
            "win_rates": {"P": 0, "B": 0, "T": 0},
            "streaks": {"P": 0, "B": 0, "T": 0},
            "patterns": {},
            "last_results": []
        }

    def create_ui(self):
        self.create_main_frames()
        self.create_buttons()
        self.create_canvas()
        self.create_statistics_panel()
        self.create_control_buttons()

    def create_main_frames(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

    def create_buttons(self):
        button_frame = ttk.LabelFrame(self.left_frame, text="Controls", padding="5")
        button_frame.pack(fill=tk.X, pady=5)
        
        for result, color in self.colors.items():
            btn = tk.Button(
                button_frame,
                text=result,
                bg=color,
                fg="white",
                width=8,
                font=("Arial", 12, "bold"),
                command=lambda r=result: self.add_result(r)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)

    def create_canvas(self):
        canvas_frame = ttk.LabelFrame(self.left_frame, text="Results Table", padding="5")
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            width=600,
            height=400,
            bg="white"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def create_statistics_panel(self):
        stats_frame = ttk.LabelFrame(self.right_frame, text="Statistics", padding="5")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        self.win_rate_labels = {}
        self.streak_labels = {}
        self.pattern_label = ttk.Label(stats_frame, text="Common Patterns:", font=("Arial", 10))
        self.pattern_label.pack(pady=5)

        pred_frame = ttk.LabelFrame(stats_frame, text="Prediction Accuracy", padding="5")
        pred_frame.pack(fill=tk.X, pady=5)

        self.accuracy_label = ttk.Label(pred_frame, text="Accuracy: 0%")
        self.accuracy_label.pack()

        self.correct_label = ttk.Label(pred_frame, text="Correct: 0")
        self.correct_label.pack()

        self.incorrect_label = ttk.Label(pred_frame, text="Incorrect: 0")
        self.incorrect_label.pack()
        
        for result in self.colors:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=2)
            
            self.win_rate_labels[result] = ttk.Label(frame, text=f"{result} Win Rate: 0%")
            self.win_rate_labels[result].pack(side=tk.LEFT)
            
            self.streak_labels[result] = ttk.Label(frame, text=f"Streak: 0")
            self.streak_labels[result].pack(side=tk.RIGHT)

        self.prediction_label = ttk.Label(
            stats_frame,
            text="Prediction: -",
            font=("Arial", 12, "bold")
        )
        self.prediction_label.pack(pady=10)

    def create_control_buttons(self):
        control_frame = ttk.Frame(self.right_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            control_frame,
            text="Reset View",
            command=self.reset_table,
            width=15
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            control_frame,
            text="Clear Session",
            command=self.clear_session,
            width=15
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            control_frame,
            text="Export Data",
            command=self.export_data,
            width=15
        ).pack(fill=tk.X, pady=2)

    def load_data(self):
        try:
            if os.path.exists(self.ml_file):
                with open(self.ml_file, "r") as f:
                    data = json.load(f)
                    self.ml_data = data.get("results", [])
                    self.timestamps = data.get("timestamps", [])
            
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.results = data.get("results", [])[-self.display_count:]
                    self.patterns = data.get("patterns", [])
                    self.prediction_stats = data.get("prediction_stats", {
                        'correct': 0,
                        'incorrect': 0,
                        'total': 0
                    })
            
            self.update_table(self.results)
            self.update_statistics()
            self.update_prediction_stats()
            self.predict_next_result()
        except Exception as e:
            messagebox.showerror("Error", f"Data load failed: {str(e)}")

    def add_result(self, result):
        if self.current_prediction:
            self.prediction_stats['total'] += 1
            if result == self.current_prediction:
                self.prediction_stats['correct'] += 1
            else:
                self.prediction_stats['incorrect'] += 1
            self.update_prediction_stats()

        timestamp = datetime.now().isoformat()
        
        self.results.append(result)
        self.ml_data.append(result)
        self.timestamps.append(timestamp)
        
        if len(self.results) > self.display_count:
            self.results = self.results[-self.display_count:]
        
        self.reset_table()
        self.update_table(self.results)
        self.update_patterns()
        self.update_statistics()
        self.save_data()
        
        self.predict_next_result()

    def predict_next_result(self):
        if len(self.ml_data) < 3:
            self.prediction_label.config(text="Prediction: Insufficient data")
            self.current_prediction = None
            return

        recent = tuple(self.ml_data[-3:])
        pattern_matches = []
        
        for i in range(len(self.ml_data) - 4):
            pattern = tuple(self.ml_data[i:i+3])
            if pattern == recent:
                pattern_matches.append(self.ml_data[i+3])

        if pattern_matches:
            self.current_prediction = Counter(pattern_matches).most_common(1)[0][0]
            confidence = len(pattern_matches) / len(self.ml_data) * 100
            pred_text = f"Prediction: {self.current_prediction} ({confidence:.1f}% confidence)"
        else:
            self.current_prediction = Counter(self.ml_data).most_common(1)[0][0]
            pred_text = f"Prediction: {self.current_prediction} (frequency-based)"
        
        self.prediction_label.config(text=pred_text)

    def update_prediction_stats(self):
        total = self.prediction_stats['total']
        if total > 0:
            accuracy = (self.prediction_stats['correct'] / total) * 100
            self.accuracy_label.config(text=f"Accuracy: {accuracy:.1f}%")
            self.correct_label.config(text=f"Correct: {self.prediction_stats['correct']}")
            self.incorrect_label.config(text=f"Incorrect: {self.prediction_stats['incorrect']}")

    def update_table(self, results):
        for idx, result in enumerate(results):
            col = idx // self.rows
            row = idx % self.rows
            self.draw_cell(col, row, result)

    def draw_cell(self, col, row, result):
        x0 = col * self.cell_size + self.padding
        y0 = row * self.cell_size + self.padding
        x1 = x0 + self.cell_size - self.padding * 2
        y1 = y0 + self.cell_size - self.padding * 2

        self.canvas.create_oval(
            x0, y0, x1, y1,
            fill=self.colors[result],
            outline="black"
        )
        self.canvas.create_text(
            (x0 + x1) / 2,
            (y0 + y1) / 2,
            text=result,
            fill="white",
            font=("Arial", 16, "bold")
        )

    def update_patterns(self):
        if len(self.results) >= 3:
            pattern = self.results[-3:]
            self.patterns.append(pattern)
            self.analyze_patterns()

    def analyze_patterns(self):
        if len(self.ml_data) >= 3:
            pattern_counts = Counter()
            for i in range(len(self.ml_data) - 2):
                pattern = tuple(self.ml_data[i:i+3])
                pattern_counts[pattern] += 1
            
            common_patterns = pattern_counts.most_common(3)
            pattern_text = "Common Patterns:\n"
            for pattern, count in common_patterns:
                pattern_text += f"{' → '.join(pattern)}: {count}\n"
            self.pattern_label.config(text=pattern_text)

    def update_statistics(self):
        if not self.ml_data:
            return

        total = len(self.ml_data)
        counts = Counter(self.ml_data)
        for result in self.colors:
            win_rate = (counts[result] / total) * 100
            self.win_rate_labels[result].config(
                text=f"{result} Win Rate: {win_rate:.1f}%"
            )

        current_streaks = {r: 0 for r in self.colors}
        max_streaks = {r: 0 for r in self.colors}
        
        for result in self.ml_data:
            for r in self.colors:
                if result == r:
                    current_streaks[r] += 1
                    max_streaks[r] = max(max_streaks[r], current_streaks[r])
                else:
                    current_streaks[r] = 0

        for result in self.colors:
            self.streak_labels[result].config(
                text=f"Max Streak: {max_streaks[result]}"
            )

    def reset_table(self):
        self.canvas.delete("all")

    def clear_session(self):
        if messagebox.askyesno("Confirm", "Clear current session and reset prediction stats?"):
            self.results.clear()
            self.patterns.clear()
            self.prediction_stats = {'correct': 0, 'incorrect': 0, 'total': 0}
            self.current_prediction = None
            self.reset_table()
            self.save_data()
            self.update_statistics()
            self.update_prediction_stats()
            messagebox.showinfo("Success", "Session cleared")

    def export_data(self):
        try:
            export_data = {
                "results": self.ml_data,
                "timestamps": self.timestamps,
                "statistics": {
                    "win_rates": {r: self.win_rate_labels[r].cget("text") for r in self.colors},
                    "streaks": {r: self.streak_labels[r].cget("text") for r in self.colors}
                },
                "prediction_stats": self.prediction_stats
            }
            
            filename = f"card_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump({
                    "results": self.results,
                    "patterns": self.patterns,
                    "prediction_stats": self.prediction_stats
                }, f)
            
            with open(self.ml_file, "w") as f:
                json.dump({
                    "results": self.ml_data,
                    "timestamps": self.timestamps
                }, f)
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {str(e)}")

def main():
    root = tk.Tk()
    root.style = ttk.Style()
    root.style.theme_use('clam')
    app = CardTableApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
