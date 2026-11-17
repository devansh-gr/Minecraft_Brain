"""Keyword -> brain region. Base forms only; the parser strips -s/-es/-ies/-ed/-ing/-ly/-er."""
LEX = {
    "prefrontal": """
should would decide decision choose choice option pick plan planning schedule future goal goals priority
why reason logic logical think thought idea ideas opinion believe belief guess predict strategy tactic
solve problem puzzle riddle smart clever genius intelligent intelligence iq wise wisdom judge judgment
moral ethics ethical right wrong fair unfair lie lying truth honest cheat trust deserve
happy sad angry anger mad upset love hate fear afraid scared scary worry worried anxious anxiety nervous
stress stressed calm relax mood emotion emotional feeling jealous envy proud pride shame guilty guilt
embarrassed lonely bored boring excited exciting motivation motivate lazy procrastinate focus attention
concentrate distract distracted discipline habit addict addiction willpower control impulse patience
money invest investment budget spend save saving business career job work boss quit hire interview
risk safe danger dangerous bet gamble win lose rich poor price worth value cost deal negotiate
personality character kind mean nice rude friend friendship relationship date crush breakup marry
advice help improve better best worse worst should meaning purpose life dream ambition
""",
    "broca": """
say said speak speech talk talking tell told pronounce pronunciation accent stutter whisper shout yell
sentence grammar verb noun adjective adverb tense plural syllable vowel consonant punctuation
translate translation spell spelling write writing essay paragraph letter rhyme poem poetry
language languages english spanish french german chinese mandarin japanese korean hindi arabic
russian italian portuguese latin bilingual fluent dialect slang vocabulary
debate argue argument explain explanation describe presentation lecture conversation chat
""",
    "motor": """
move movement run sprint jog walk jump hop skip climb crawl swim dive throw toss kick punch hit
push pull lift carry drag grab grip hold catch squeeze stretch bend twist spin turn roll flip
dance wave clap point nod blink chew swallow breathe stand sit kneel lean reach press tap type
draw paint sculpt build cut sew knit cook stir chop pour write
sport sports soccer football basketball baseball tennis hockey volleyball golf boxing wrestling
karate gym workout exercise muscle muscles strong strength fast speed sprint athlete marathon
hand hands arm arms leg legs foot feet finger fingers toe toes shoulder knee elbow wrist
reflex fidget shake tremble twitch paralyzed
""",
    "somato": """
feel touch touching hot cold warm cool freezing burning burn heat chill pain painful hurt ache sore
itch itchy tickle tickly scratch rub massage pinch poke sting sharp dull pressure squeeze
soft hard rough smooth bumpy fuzzy fluffy furry silky sticky slimy wet dry slippery texture
temperature skin numb tingle tingling prickly sensitive sensation feeling hug kiss cuddle
injury injure bruise cut wound bleed fever sick hungry thirsty tired full stomach
""",
    "parietal": """
plus minus times divide divided multiply multiplication division add addition subtract subtraction
math maths arithmetic algebra calculus geometry equation formula solve calculate calculation compute
number numbers count counting many much amount total sum difference product quotient equal equals
half double triple quarter third percent percentage fraction decimal ratio average square root
zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen
sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred
thousand million billion trillion infinity odd even prime
where direction left north south east west map maps navigate navigation route path location
distance far near close between above below behind inside outside position place space spatial
size big bigger small smaller large tall short wide long length width height area volume weight
heavy light measure meter mile inch foot kilometer angle degree rotate rotation physics speed
minute hour clock time timer
# ## ### #### ##### ######
""",
    "temporal": """
hear heard listen sound sounds noise noisy loud quiet silent silence echo ring beep buzz
music song songs sing singing melody rhythm beat lyrics band concert album artist rap pop rock
jazz classical hiphop voice voices tone pitch ear ears deaf
word words mean meaning means define definition dictionary synonym understand comprehend
name names remember memory memories memorize forget forgot recall remind nostalgia
yesterday ago past history historical ancient war king queen president capital country city
when who fact facts know knowledge trivia learn learning study school teacher test exam quiz
story stories book books movie film show character characters
face faces recognize person people friend family mom dad mother father brother sister grandma
animal animals dog dogs cat cats bird horse lion tiger elephant fish
planet earth moon space star stars science biology chemistry history geography
""",
    "occipital": """
see seen saw look looking watch watching view stare glance notice spot visible invisible
color colour colors red orange yellow green blue purple pink brown black white gray grey gold silver
bright dark darkness light shine shiny glow glowing sparkle shadow shade
picture photo image video painting art artist drawing sketch cartoon anime comic design
shape shapes circle square triangle rectangle pattern stripe dot line curve
read reading text font sign letters
eye eyes vision visual sight blind glasses camera lens mirror screen pixel
sky sun sunset sunrise rainbow cloud clouds ocean sea beach mountain flower flowers tree forest
pretty beautiful ugly cute handsome style outfit fashion wear look
""",
    "cerebellum": """
balance balanced coordination coordinate steady stable wobble dizzy dizziness vertigo fall falling trip
ride riding bike bicycle skate skating skateboard snowboard surf surfing ski skiing scooter unicycle
juggle juggling tightrope gymnastics cartwheel handstand backflip parkour yoga
timing rhythm tempo drum drums piano guitar violin instrument
practice skill skills muscle-memory reflexes smooth precise precision aim accuracy accurate
typing tie shoelace
""",
}
