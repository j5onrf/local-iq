#!/usr/bin/env bash
# Functional Inline Media Controller (Pure Reactive)

if ! command -v playerctl >/dev/null 2>&1; then
    echo -e " \033[1;31mError:\033[0m playerctl is not installed."
    exit 1
fi

cleanup() {
    echo -ne "\033[?25h" # Restore cursor
    stty sane 2>/dev/null
}
trap 'cleanup; exit 0' INT TERM EXIT

echo -ne "\033[?25l" # Hide cursor
stty -icanon -echo min 0 time 0 2>/dev/null

first_run=true

render_frame() {
    if ! playerctl status >/dev/null 2>&1; then
        if [ "$first_run" = true ]; then
            echo -e " \033[90m♫ Idle\033[0m"
            echo -e " \033[90m[ No active system media player detected ]\033[0m"
        else
            echo -ne "\033[2A\033[K"
            echo -e " \033[90m♫ Idle\033[0m"
            echo -e " \033[90m[ No active system media player detected ]\033[0m\033[K"
        fi
        first_run=false
    else
        ACTIVE_PLAYER=$(playerctl -l 2>/dev/null | head -n 1)
        STATUS=$(playerctl status 2>/dev/null)
        TITLE=$(playerctl metadata title 2>/dev/null)
        ARTIST=$(playerctl metadata artist 2>/dev/null)

        TRACK_STRING="$TITLE"
        [[ -n "$ARTIST" ]] && TRACK_STRING="$ARTIST - $TITLE"

        TRACK_STRING="${TRACK_STRING% - YouTube}"
        TRACK_STRING="${TRACK_STRING% - YouTube Music}"
        TRACK_STRING="${TRACK_STRING% - Spotify}"

        TERM_WIDTH=$(tput cols 2>/dev/null || echo 80)
        MAX_LEN=$(( TERM_WIDTH - 12 ))
        if [ ${#TRACK_STRING} -gt $MAX_LEN ]; then
            TRACK_STRING="${TRACK_STRING:0:$((MAX_LEN-3))}..."
        fi

        VOL_PCT="100"
        if command -v wpctl >/dev/null 2>&1; then
            WP_OUT=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null)
            if [[ "$WP_OUT" =~ ([0-9\.]+) ]]; then
                VOL_PCT=$(awk "BEGIN {print int(${BASH_REMATCH[1]} * 100)}")
            fi
        fi

        if [[ "$STATUS" == "Playing" ]]; then
            STATUS_BADGE="\033[1;45;30m Playing \033[0m"
        else
            STATUS_BADGE="\033[1;42;30m Paused \033[0m"
        fi

        if [ "$first_run" = false ]; then
            echo -ne "\033[2A"
        fi
        first_run=false

        echo -e " \033[1;32m♫\033[0m \033[1m${TRACK_STRING}\033[0m\033[K"
        echo -e " \033[90mVOL:\033[0m ${VOL_PCT}%  │  \033[90mSRC:\033[0m ${ACTIVE_PLAYER%%.*}  │  ${STATUS_BADGE}\033[K"
    fi
}

# Draw initial state snapshot
render_frame

while true; do
    IFS= read -r -s -n 1 key

    case "$key" in
        " " | "") # Play/Pause Toggle
            if playerctl status >/dev/null 2>&1; then
                if [[ "$ACTIVE_PLAYER" == *spotify* ]] && command -v xdotool >/dev/null 2>&1; then
                    xdotool key XF86AudioPlay
                else
                    playerctl play-pause
                fi
            fi
            ;;
        "+"|"="|"}"|"]") # Volume Up (Catches shifted and unshifted keys)
            if command -v wpctl >/dev/null 2>&1; then
                wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+
            fi
            ;;
        "-"|"{"|"[") # Volume Down
            if command -v wpctl >/dev/null 2>&1; then
                wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
            fi
            ;;
        "n"|"N") # Next Song
            playerctl next 2>/dev/null
            ;;
        "p"|"P") # Previous Song
            playerctl position 0 2>/dev/null
            playerctl previous 2>/dev/null
            ;;
        "q"|"Q"|$'\e') # Quit out
            break
            ;;
    esac

    render_frame
done

# Wipe lines cleanly back into your shell prompt layout
echo -ne "\033[2A\033[J"
