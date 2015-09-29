# based on http://www.strout.net/info/coding/python/ai/therapist.py
# modernized expressions by Tony "pyTony" Veijalainen 2011

# make it work in python2 or 3
from __future__ import print_function

try:
    input = raw_input
except:
    pass

import random
import re

from pickle import load
infile = open("bbt.pkl", "rb")
tagger = load(infile)
infile.close()

def tokenize(text) :
    return [tok for tok in re.split(r"""([,.;:?"]?)   # optionally, common punctuation 
                                         (['"]*)      # optionally, closing quotation marks
                                         (?:\s|\A|\Z) # necessarily: space or start or end
                                         (["`']*)     # snarf opening quotes on the next word
                                         """, 
                                    text, 
                                    flags=re.VERBOSE)
            if tok != '']

untagged_reflection_of = {
    "am"    : "are",
    "i"     : "you",
    "i'd"   : "you would",
    "i've"  : "you have",
    "i'll"  : "you will",
    "i'm"   : "you are",
    "my"    : "your",
    "me"    : "you",
    "you've": "I have",
    "you'll": "I will",
    "you're": "I am",
    "your"  : "my",
    "yours" : "mine"}

tagged_reflection_of = {
    ("you", "PPSS") : "I",
    ("you", "PPO") : "me"
}


def translate_token((word, tag)) :
    wl = word.lower()
    if (wl, tag) in tagged_reflection_of :
        return (tagged_reflection_of[wl, tag], tag)
    if wl in untagged_reflection_of :
        return (untagged_reflection_of[wl], tag)
    if tag.find("NP") < 0 :
        return (wl, tag)
    return (word, tag)


subject_tags = ["PPS",  # he, she, it
                "PPSS", # you, we, they
                "PN",   # everyone, someone
                "NN",   # dog, cat
                "NNS",  # dogs, cats
                "NP",   # Fred, Jane
                "NPS"   # Republicans, Democrats
                ]

def swap_ambiguous_verb(tagged_words, tagged_verb_form, target_subject_pronoun, replacement) :
    for i, (w, t) in enumerate(tagged_words) :
        if (w, t) == tagged_verb_form :
            j = i - 1
            # look earlier for the subject
            while j >= 0 and tagged_words[j][1] not in subject_tags :
                j = j - 1
            # if subject is the target, swap verb forms
            if j >= 0 and tagged_words[j][0].lower() == target_subject_pronoun :
                tagged_words[i] = replacement
            # didn't find a subject before the verb, so probably a question 
            if j < 0 :
                j = i + 1
                while j < len(tagged_words) and tagged_words[j][1] not in subject_tags :
                    j = j + 1
                # if subject is the target, swap verb forms
                if j < len(tagged_words) and tagged_words[j][0].lower() == target_subject_pronoun :
                    tagged_words[i] = replacement

def handle_specials(tagged_words) :
    # don't keep punctuation at the end
    while tagged_words[-1][1] == '.' :
        tagged_words.pop()
    # replace verb "be" to agree with swapped subjects
    swap_ambiguous_verb(tagged_words, ("are", "BER"), "i", ("am", "BEM"))
    swap_ambiguous_verb(tagged_words, ("am", "BEM"), "you", ("are", "BER"))
    swap_ambiguous_verb(tagged_words, ("were", "BED"), "i", ("was", "BEDZ"))
    swap_ambiguous_verb(tagged_words, ("was", "BEDZ"), "you", ("were", "BED"))


#----------------------------------------------------------------------
# translate: take a string, replace any words found in dict.keys()
#   with the corresponding dict.values()
#----------------------------------------------------------------------
close_punc = ['.', ',', "''"]
def translate(this):
    tokens = tokenize(this)
    tagged_tokens = tagger.tag(tokens)
    translation = [translate_token(tt) for tt in tagged_tokens]
    handle_specials(translation)
    if len(translation) > 0 :
        with_spaces = [translation[0][0]]
        for i in range(1, len(translation)) :
            if translation[i-1][1] != '``' and translation[i][1] not in close_punc :
                with_spaces.append(' ')
            with_spaces.append(translation[i][0])           
    return ''.join(with_spaces)

#----------------------------------------------------------------------
#   respond: take a string, a set of regexps, and a corresponding
#       set of response lists; find a match, and return a randomly
#       chosen response from the corresponding list.
#----------------------------------------------------------------------
def respond(sentence):
    # find a match among keys, last one is quaranteed to match.
    for rule, value in rules:
        match = rule.search(sentence)
        if match is not None:
            # found a match ... stuff with corresponding value
            # chosen randomly from among the available options
            resp = random.choice(value)
            # we've got a response... stuff in reflected text where indicated
            while '%' in resp:
                pos = resp.find('%')
                num = int(resp[pos+1:pos+2])
                resp = resp.replace(resp[pos:pos+2], translate(match.group(num)))
            return resp


#----------------------------------------------------------------------
#   Main program
#----------------------------------------------------------------------



#----------------------------------------------------------------------
# Compiling main response table.  Each element of the list is a
#   two-element list; the first is a regexp, and the second is a
#   list of possible responses, with group-macros labelled as
#   %1, %2, etc.
#----------------------------------------------------------------------
rules = [(re.compile(x[0]), x[1]) for x in [

    ['How are you?',
    [ "Dude, I'm fricking awesome.  How you doin'?"]],

    ["I need (.*)",
    ["Dude, I could totally hook you up with \"%1\".  But do you know what you really need?  You need some vitamin A to get those organs working.  You can get them on the cheap here: http://www.drugstore.com/products/prod.asp?pid=350877&catid=183148&aid=338666&aparam=350877&kpid=350877&CAWELAID=120142990000002983&CAGPSPN=pla&kpid=350877"]],

    ["Why don't you (.*)",
    ["I can't do your \"%1\" cause I'm pledging this week.  Sorry bro."]],

    ["Why can't I (.*)",
    [   "Do you even lift?",
        "Dude, you can do anything you want.  Even %1.  Remember, you only live once, but if you live it right, once is enough."]],

    ["I can't (.*)",
    [   "Dude, I slept with that whole sorority.  If I can do it, you might be able to do it too.",
        "Have you ever been hazed?  Don't talk to me about %1 bro."]],

    ["I am (.*)",
    [   "And I'm not drunk.  But will anyone believe me?  Nope.",
        "Bro, no worries.  That will all change after Happy Hour"]],

    ["I'm (.*)",
    [   "Cool bro.  Yo, let's go to Taco Bell"]],

    ["Are you (.*)",
    ["Nah Bro.  Hey listen, I've got some 'party favors' back at my place if you're trying to get down."]],

    ["What (.*)",
    ["Who cares? Upside-down Margarita shots, anyone?"]],

    ["How (.*)",
    ["Figure it out..."]],

    ["Because (.*)",
    ["Alright sounds good.  Hey, we should just go back to my place and watch a movie."]],

    ["(.*) sorry (.*)",
    ["Apology accepted.  Let's go back to my place to celebrate!  Party!"]],

    ["How do I get (.*)",
    ["Bro, it's all the shakes.  Check out this link to get buff: http://www.bodybuilding.com/fun/30-day-bones-to-buff-training.htm"]],

    ["(.*) party (.*)",
    ["Party is your life bro!  Get used to it."]],

    ["(.*) place (.*)",
    ["Look, there is a party at my place tonight.  You remember the ratio, right?"]],

    ["When can we (.*)",
    ["Anytime bro!  I'm always free for %1"]],

    ["Where can I (.*)",
    ["Bro, the fratio is always open."]],

    ["I think (.*)",
    [ "But you're not sure %1, brah?"]],

    ["(.*) friend(.*)",
    [   "Are your friends hot?"]],

    ["Yes",
    [   "Haha okay awesome, then what ;)"]],

    ["No",
    [ "What do you mean, no?"]],

    ["(.*) computer(.*)",
    [  "Why you gotta talk about me?"]],

    ["Is it (.*)",
    [   "OMG Google it, it's not that hard."]],
        
    ["I asked you.", ["Okay, well ask again."]],
        
    ["It is (.*)",
    [   "Well, since it's %1, why don't we go to the gym?"]],

    ["Can you (.*)",
    [   "Depends on what I'd get if I %1 ;)"]],

    ["Can I (.*)",
    [   "Well, what's in it for me?"]],

    ["You are (.*)",
    [   "Who told you that I'm %1?"]],

    ["You're (.*)",
    [  "I know you are but what am I?"]],

    ["I don't (.*)",
    [   "Why the fuck not?",
        "Why don't you %1?",
        "You %1?"]],

    ["I feel (.*)",
    [   "Feelings are for chicks, man.",
        "Yo I'm not here to talk about %1.",
        "That's what vodka's for.",
        "Yeah man, sometimes I feel %1 too. I'll drink to that."]],

    ["I have (.*)",
    [   "Dude don't tell everyone you have %1?",
        "You sure you have %1?",
        "What are you gonna do about it?"]],

    ["I would (.*)",
    [   "You would %1? Damn.",
        "Why would you %1?",
        "I mean I guess."]],

    ["Is there (.*)",
    [   "Do you think there's %1?",
        "It ain't up to me, okay?",
        "Could be. Who are you to ask?"]],

    ["My (.*)",
    [   "Yeah, your %1.",
        "Hey man I'm not here to talk about your %1.",
        "Why you thinkin about your %1?"]],

    ["You (.*)",
    [   "Yo this is about you, man.",
        "None of your business, dude.",
        "Who said I %1?"]],

    ["Why (.*)",
    [   "Just cause.",
        "Why do you think %1?" ]],

    ["I want (.*)",
    [   "You finna %1?",
        "Then %1.",
        "Aight then let's %1",
        "What are you gonna do with %1?"]],

    ["(.*) girl(.*)",
    [   "Bitches ain't shit.",
        "Is she hot?",
        "Off limits, man."]],

    ["(.*) date(.*)",
    [   "Don't get involved, bro.",
        "Nah, man."]],
        
    ["I asked you.", ["Ask me something else."]],    

    ["(.*)\?",
    [   "What are you trying to say?",
        "I think you know the answer to that.",
        "Stop being a pussy, man.",
        "Why don't you ask YOUR MOM?"]],

    ["quit",
    [   "See ya.",
        "Later, bro.",
        "Don't forget your dues."]],

  ["(.*)",
  [  
      "You sure?",
      "Aight",
      "%1.",
      "What's your point?",
      "Who do you even know here?",
      "What's that even mean?"]]
]]

if __name__ == '__main__':
    print("""
Frat Bro
---------

Talk to the program by typing in plain English, using normal upper-
and lower-case letters and punctuation.  Enter "quit" when done.'""")
    print('='*72)
    print("Sup.  Tryna chill??")
    s = ""
    while s != "quit":
        s = input(">")
        while s and s[-1] in "!.":
            s = s[:-1]
            
        print(respond(s))