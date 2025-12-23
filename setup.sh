#!/bin/bash

# 1. Get the local IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

# 2. Define the output filename
OUTPUT_FILE="run_react_native.sh"

# 3. Create the new .sh file with the command
echo "REACT_NATIVE_PACKAGER_HOSTNAME=$IP_ADDR npx expo start -c --lan" > $OUTPUT_FILE

# 4. Make the newly created file executable
chmod +x $OUTPUT_FILE

echo "Success! Created $OUTPUT_FILE with IP: $IP_ADDR"
echo "You can now run: ./$OUTPUT_FILE"