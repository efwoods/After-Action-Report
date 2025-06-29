import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === File paths ===
root_path = os.getenv("REPORT_ROOT_PATH")
clockify_csv = "Clockify_Time_Report_Summary_06_22_2025-06_28_2025.csv"
firefox_csv = "firefox_history_last_week.csv"
github_csv = "github_commit_history.csv"
todo_csv = "Personal Project To-Do List c8469bdef0e4493d8777a4cd358822f0_all.csv"

# === Load DataFrames ===
df_clockify = pd.read_csv(os.path.join(root_path, clockify_csv))
df_firefox = pd.read_csv(os.path.join(root_path, firefox_csv))
df_github = pd.read_csv(os.path.join(root_path, github_csv))
df_todo = pd.read_csv(os.path.join(root_path, todo_csv))

# === Normalize Dates ===


def normalize_datetime(df, column_name):
    df[column_name] = pd.to_datetime(df[column_name], errors="coerce")
    return df.dropna(subset=[column_name])


df_firefox = normalize_datetime(df_firefox, "visit_time")
df_github = normalize_datetime(df_github, "date")
df_todo = normalize_datetime(df_todo, "Date Created")


def make_naive_utc(df, column):
    df[column] = pd.to_datetime(df[column], errors="coerce")

    def to_naive(x):
        if pd.isna(x):
            return pd.NaT
        if hasattr(x, "tzinfo") and x.tzinfo is not None:
            return x.tz_convert("UTC").tz_localize(None)
        else:
            return x

    df[column] = df[column].apply(to_naive)
    return df


df_firefox = make_naive_utc(df_firefox, "visit_time")
df_github = make_naive_utc(df_github, "date")
df_todo = make_naive_utc(df_todo, "Date Created")

# For Clockify, no datetime column — add NaT timestamp for sorting (optional: set to today's date)
df_clockify["timestamp"] = pd.NaT

# === Standardize Columns for LLM ===


def format_event(df, source, time_col, desc_cols):
    df = df.copy()
    df["source"] = source
    df["timestamp"] = df[time_col]
    df["description"] = df[desc_cols].astype(str).agg(" | ".join, axis=1)
    return df[["timestamp", "source", "description"]]


clockify_events = format_event(
    df_clockify,
    "clockify",
    "timestamp",  # NaT values
    ["Project", "Client", "Description", "Time (h)", "Amount (USD)"],
)
firefox_events = format_event(
    df_firefox,
    "firefox",
    "visit_time",
    ["title", "url"],
)
github_events = format_event(df_github, "github", "date", ["repo", "message", "url"])
todo_events = format_event(
    df_todo, "todo", "Date Created", ["Name", "Status", "Tags", "URL"]
)

# === Combine All Events ===

all_events = pd.concat(
    [clockify_events, firefox_events, github_events, todo_events], ignore_index=True
)
all_events.sort_values("timestamp", inplace=True, na_position="last")  # NaT last

# === Export for LLM-friendly JSONL or Markdown ===
jsonl_path = os.path.join(root_path, "weekly_productivity_events.jsonl")
markdown_path = os.path.join(root_path, "weekly_productivity_events.md")

# Save JSONL
all_events.to_json(jsonl_path, orient="records", lines=True, date_format="iso")
print(f"JSONL exported to {jsonl_path}")

# Save Markdown
with open(markdown_path, "w") as f:
    f.write("# Weekly Productivity Summary\n\n")
    for _, row in all_events.iterrows():
        ts = row["timestamp"]
        ts_str = ts.isoformat() if pd.notnull(ts) else "No timestamp"
        f.write(f"## {ts_str}\n")
        f.write(f"**Source**: {row['source']}\n\n")
        f.write(f"{row['description']}\n\n---\n")
print(f"Markdown exported to {markdown_path}")
