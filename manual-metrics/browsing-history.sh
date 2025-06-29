

PROFILE_PATH="$HOME/snap/firefox/common/.mozilla/firefox/91t1zslj.default"
SQLITE_DB="$PROFILE_PATH/places.sqlite"
OUTPUT_PATH="$HOME/gh/projects/Personal-Time-Metrics-Applications/After-Action-Report/manual-metrics/firefox_history_last_week.csv"

# Copy the database to avoid lock issues
cp "$SQLITE_DB" /tmp/places_backup.sqlite

# Extract the history
sqlite3 /tmp/places_backup.sqlite <<EOF
.headers on
.mode csv
.output $OUTPUT_PATH
SELECT datetime(moz_historyvisits.visit_date/1000000,'unixepoch','localtime') AS visit_time,
       moz_places.url,
       moz_places.title
FROM moz_places
JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id
WHERE visit_date > strftime('%s','now','-7 days') * 1000000
ORDER BY visit_date DESC;
EOF