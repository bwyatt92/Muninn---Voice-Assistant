#!/bin/bash

# Diagnose audio files in the recordings directory

RECORDINGS_DIR="/home/bw/muninn/muninn-v3/recordings"

echo "🔍 Diagnosing audio files in $RECORDINGS_DIR"
echo "=========================================="
echo ""

cd "$RECORDINGS_DIR" || exit 1

for file in web_recording_*.wav; do
    if [ -f "$file" ]; then
        echo "📁 File: $file"
        echo "   Size: $(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null) bytes"
        echo "   First 16 bytes (hex): $(xxd -l 16 -p "$file" | tr -d '\n')"
        echo "   File type: $(file "$file")"

        # Try to get audio info with ffprobe
        if command -v ffprobe &> /dev/null; then
            echo "   FFprobe info:"
            ffprobe -v quiet -print_format json -show_format -show_streams "$file" 2>&1 | grep -E "codec_name|duration|sample_rate|channels" | sed 's/^/     /'
        fi

        echo ""
    fi
done

echo "=========================================="
echo "✅ Diagnosis complete"
