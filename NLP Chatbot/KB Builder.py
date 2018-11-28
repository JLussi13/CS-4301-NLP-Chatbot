import textrazor, sqlite3, os
from nltk import word_tokenize, sent_tokenize, SnowballStemmer
stemmer = SnowballStemmer('english')
db_file = "ChatbotKB.db"
keyword_file = "\Important Terms.txt"
relations_path = "\Term Content\Term Relations\\"

def main():
    conn = create_connection(db_file)
    with conn:
        c = conn.cursor()
        insert_content(c, keyword_file)


def create_connection(file_name):
    try:
        conn = sqlite3.connect(file_name)
        return conn
    except sqlite3.Error as e:
        print(e)
    return None


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


def insert_content(c, keyword_file):
    c.execute('DELETE FROM keywords')
    c.execute('DELETE FROM relations')
    file = open(os.getcwd() + keyword_file, 'r', encoding='utf8')
    term_content = file.read()
    term_content = word_tokenize(term_content)
    rowid = []
    for term in term_content:
        c.execute('INSERT INTO keywords(keyword) VALUES(?)', [term])
        with open(os.getcwd() + relations_path + stemmer.stem(term) + 'Relations.txt', 'r', encoding='utf8') as f:
            sentContent = f.read()
            sentContent = sentContent.splitlines()
            sentence = None
            predicate = None
            obj = None
            subject = None
            for sent in sentContent:
                if 'SUBJECT' in sent:
                    sent = sent.replace('SUBJECT ', '')
                    subject = sent
                elif 'PREDICATE' in sent:
                    sent = sent.replace('PREDICATE ', '')
                    predicate = sent
                elif 'OBJECT' in sent:
                    sent = sent.replace('OBJECT ', '')
                    obj = sent
                elif 'SENTENCE' in sent:
                    sent = sent.replace('SENTENCE ', '')
                    sentence = sent
                    if c.execute("SELECT count(*) FROM relations WHERE sentence=?", (sentence, )).fetchone()[0] == 0:
                        c.execute('INSERT INTO relations(sentence, subject, predicate, object) VALUES(?,?,?,?)',
                                  [sentence, subject, predicate, obj])
                    sentence = None
                    predicate = None
                    obj = None
                    subject = None

    for fileName in os.listdir(os.getcwd() + relations_path):
        file_content = open(os.getcwd() + relations_path + '/' + fileName).read().split("\n")



if __name__ == '__main__':
    main()
