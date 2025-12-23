#!/bin/bash

# 1. Get the name from app.json
APP_NAME=$(grep -m 1 -o '"name": *"[^"]*"' app.json | cut -d '"' -f 4 | tr -d ' ')

if [ -z "$APP_NAME" ]; then
    echo "Warning: Could not find name in app.json. Falling back to folder name."
    APP_NAME=$(basename "$(pwd)" | tr -d ' ')
fi

# 2. Capture paths
FULL_PATH=$(pwd)
DIR_NAME=$(basename "$FULL_PATH")

# 3. Define output file
OUTPUT_FILE="sync_command.sh"

# 4. Generate the content
cat <<EOF > $OUTPUT_FILE
sync create --name=$APP_NAME \\
    $FULL_PATH \\
    macos@localhost:2222:~/src/$DIR_NAME \\
    --ignore="node_modules" \\
    --ignore=".expo" \\
    --ignore=".git" \\
    --symlink-mode=posix-raw
EOF

chmod +x $OUTPUT_FILE

echo "✅ Success!"
echo "Extracted & Cleaned Name: $APP_NAME"
echo "Generated: $OUTPUT_FILE"

# Run the script and clean up
./$OUTPUT_FILE
rm $OUTPUT_FILE
rm setup_sync.sh