from nltk import word_tokenize, sent_tokenize, pos_tag, SnowballStemmer
from nltk.corpus import stopwords
import sqlite3, sys, os, random, enum
from sqlite3 import Error
from difflib import SequenceMatcher
stop_words = set(stopwords.words('english'))
stemmer = SnowballStemmer('english')
db = "ChatbotKB.db"

GREETING_KEYWORDS = ["hello", "hi", "greetings", "sup", "what's up"]
POSITIVE_WORDS = open(os.getcwd() + '\positive-words.txt', 'r', encoding='utf8').read().split("\n")
# Use when no other placeholder response fits
DEFAULT_RESPONSE = "I don't understand, why not ask me about "
# Use when greeted by the user
GREETING_RESPONSE = "Hello there, why not ask me about "
# Use when user asks about the bot
SELF_REFERENCE_RESPONSE = "There's not much to me, why not ask me about "
# Use when user wants bot's opinion on themselves
USER_REFERENCE_RESPONSE = "I don't know you, but I do know sustainability. Why not ask me about "
# Use when the user inquires what the bot knows
BOT_INQUIRY_RESPONSE = "I have a specialty in the following subjects pertaining to sustainability: "
# When the user does not make an inquiry
NO_INQUIRY_RESPONSE = "Can you frame that into a question?"
# When user chooses a subject but the inquiry has no hits
NO_HITS_RESPONSE = "I don't quite understand you or don't have a response, but here's a random fact about "

IMPORTANT_TERMS = ['business', 'development', 'economy', 'ecology', 'environment', 'humans', 'green', 'resources',
                   'management', 'sustainability', 'nature']
IMPORTANT_TERMS_STEMMED = ['busi', 'develop', 'econom', 'economi', 'energi', 'environment', 'environ', 'resource',
                           'resourc', 'sustain', 'sustainable', 'human', 'ecolog', 'green',
                           'manag', 'natur']
GREETING_SENTENCE = "Hello, I am a chatbot with a specialty in sustainability. I am meant for people who know " \
                    "nothing about sustainability. What do you wish to know about sustainability?"

POSITIVE_THRESHOLD = .25

class KBParts(enum.Enum):
    SENTENCE = 1
    SUBJECT = 2
    PREDICATE = 3
    OBJECT = 4

def main():
    sent = input(GREETING_SENTENCE)
    while True:
        sent = input(respond(sent))


def respond(sentence):
    word_tokens = word_tokenize(sentence)
    pos_tags = pos_tag(word_tokens)
    term = check_for_term(sentence)

    if term is None:
        return get_mismatch_response(pos_tags)
    else:
        rows = select_subject_from_database(stemmer.stem(term))
        return choose_term_response(rows, pos_tags, term, sentence)


def get_mismatch_response(pos_tags):
    inquiry = False
    pronouns = []
    verbs = []
    for tags in pos_tags:
        word = tags[0].lower()
        if tags[1] == 'WP' or tags[1] == 'WRB' or tags[1] == 'WDT':
            inquiry = True
        if tags[1] == 'PRP':
            pronouns.append(word)
        if tags[1] == 'VB':
            verbs.append(word)
    if inquiry and 'me' in pronouns and 'you' in pronouns and pronouns.index('you') < pronouns.index('me'):
        if 'know' in verbs or 'tell' in verbs:
            return BOT_INQUIRY_RESPONSE + ', '.join(IMPORTANT_TERMS)
        else:
            return USER_REFERENCE_RESPONSE + random.choice(IMPORTANT_TERMS)
    elif inquiry and 'i' in pronouns and 'you' in pronouns and pronouns.index('you') < pronouns.index('i'):
        return USER_REFERENCE_RESPONSE + random.choice(IMPORTANT_TERMS)
    elif inquiry and 'i' in pronouns and 'you' in pronouns and pronouns.index('i') < pronouns.index('you'):
        return SELF_REFERENCE_RESPONSE + random.choice(IMPORTANT_TERMS)
    elif inquiry and ('you' in pronouns or 'yourself' in pronouns):
        return SELF_REFERENCE_RESPONSE + random.choice(IMPORTANT_TERMS)
    elif inquiry:
        return DEFAULT_RESPONSE + random.choice(IMPORTANT_TERMS)
    else:
        return NO_INQUIRY_RESPONSE


def check_for_greeting(sentence):
    sent_words = word_tokenize(sentence)
    for word in sent_words:
        if word.lower() in GREETING_KEYWORDS:
            return GREETING_RESPONSE + random.choice(IMPORTANT_TERMS)
    return None


def check_for_term(sentence):
    sent_words = word_tokenize(sentence)
    for word in sent_words:
        word_stemmed = stemmer.stem(word)
        if word_stemmed in IMPORTANT_TERMS_STEMMED:
            return word
    return None


def choose_term_response(rows, pos_tags, subject, input_sent):
    inquiry = False
    about_subject = False
    define_subject = False
    user_how = False
    user_why = False
    pronoun_list = []
    noun_list = []
    verb_list = []
    inquiry_list = []
    for tags in pos_tags:
        word = tags[0].lower()
        if tags[1] == 'WP' or tags[1] == 'WRB' or tags[1] == 'WDT':
            inquiry_list.append(word)
            inquiry = True
        if tags[1] == 'NN':
            noun_list.append(word)
        if 'V' in tags[1]:
            verb_list.append(word)
        if tags[1] == 'PRP':
            pronoun_list.append(word)
    if inquiry:
        if 'why' in inquiry_list:
            user_why = True
        elif 'how' in inquiry_list:
            user_how = True
    elif 'define' in verb_list or \
            (('does' in verb_list and 'mean' in verb_list) and inquiry)\
            or ('is' in verb_list and inquiry):
        define_subject = True
    else:
        about_subject = True
    chosen_responses = []
    sents = []
    for row in rows:
        sents.append(row[1])
        if define_subject and 'is' in row[3]:
            chosen_responses.append(row[1])
        elif user_why and ('huma' in row[4]):
            chosen_responses.append(row[1])
        else:
            sent = row[1]
            tokens = word_tokenize(sent)
            token_count = 0
            positive_token_count = 0
            for token in tokens:
                if token not in stop_words:
                    token_count += 1
                    if token in POSITIVE_WORDS:
                        positive_token_count += 1
            if (positive_token_count / token_count) > POSITIVE_THRESHOLD:
                chosen_responses.append(sent)
    if chosen_responses.__len__() == 0:
        return NO_HITS_RESPONSE + subject + ": " + random.choice(sents)
    else:
        match = 0.0
        chosen_response = ""
        for sent in chosen_responses:
            if SequenceMatcher(a=sent, b=input_sent).ratio() > match:
                match = SequenceMatcher(a=sent, b=input_sent).ratio()
                chosen_response = sent
        return random.choice(chosen_responses)


def select_subject_from_database(subject):
    conn = create_connection(db)
    cur = conn.cursor()
    subject = "%" + subject + "%"
    cur.execute("SELECT * FROM relations WHERE subject LIKE ?", (subject, ))
    rows = cur.fetchall()
    conn.close()
    return rows


def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


if __name__ == "__main__":
    main()