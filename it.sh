docker rm -vf $(docker ps -a -f name=GAME -q)
mapfile -t maps < <(find ~/.scbw/maps/sscai -name '*.sc?' -printf "sscai/%P\n")
pids=()

function play() {
    (
        trap "" HUP
        game_name="IT_${1// /_}"
        rm -rf ~/.scbw/games/GAME_$game_name
        map=${maps[$RANDOM % ${#maps[@]} ]}
        scbw.play --headless --bots "Marine Hell" "$1" --map "$map" --game_name "$game_name" --timeout_at_frame 86400
  ) &
  pids[${#pids[*]}]=$!
}


#play Stardust
#play PurpleWave
#play BananaBrain
#play Steamhammer
#play "Bryan Weber"
#play "Tomas Cere"
#play "Soeren Klett"
#play "Marek Kadek"
#play "KaonBot"
#play "Black Crow"
#play "Yuanheng Zhu"
play "Jakub Trancik"

for pid in ${pids[*]}; do
    wait $pid
done

find ~/.scbw/games -name 'result.json' | grep 'GAME_IT' | xargs grep 'is_crashed": true' > /dev/null
if [ $? -ne 0 ]; then
    echo "Failed"
fi
