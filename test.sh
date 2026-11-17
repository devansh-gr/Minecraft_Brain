F=build/datapack/redstone_cortex/data/brain/function/cortex
pos(){ head -1 $F/$1_on.mcfunction | awk '{print $2,$3,$4}'; }
ask(){ python3 rcon.py "data merge block 14 -59 -8 {front_text:{messages:[$1]}}" "function brain:read" >/dev/null; sleep 9; }
lit(){ out=""; for r in prefrontal broca motor somato parietal temporal occipital cerebellum; do python3 rcon.py "execute if block $(pos $r) redstone_block" | grep -q passed && out="$out $r"; done; echo "$out"; }
for q in '"what is seven","times eight?","",""' '"What COLOR is","the sky when I","feel sad?",""' '"can you hear","and see it","",""' '"xyzzy","","",""' '"how do i ride","a bike and","keep balance",""' '"should i quit","my job","",""'; do ask "$q"; echo "$q ->$(lit)"; done
read x y z <<< "$(pos prefrontal)"; python3 rcon.py "execute if block $((x+1)) $y $z redstone_lamp[lit=true]" "execute if block $((x-1)) $y $z redstone_lamp[lit=true]" "execute if block $x $((y+1)) $z redstone_lamp[lit=true]" "execute if block $x $((y-1)) $z redstone_lamp[lit=true]" "execute if block $x $y $((z+1)) redstone_lamp[lit=true]" "execute if block $x $y $((z-1)) redstone_lamp[lit=true]" | grep -c passed
sleep 12; echo "after timeout ->$(lit)"
