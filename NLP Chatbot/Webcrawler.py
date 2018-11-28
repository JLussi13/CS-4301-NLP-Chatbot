import requests, io, re, os, textrazor, json, string
from nltk import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from bs4 import BeautifulSoup
textrazor.api_key = "64b3ce6498628a3181e5eb1df58b0207ad139d8ea001bbe43fa3267b"

stopWords = set(stopwords.words('english'))
starterURLs = ['https://www.google.com/search?q=sustainability&ie=utf-8&oe=utf-8&client=firefox-b-1-ab']
notInclude = ['google', 'Google', 'post',]
MAX_LINKS = 100
LINKS_PER_PAGE = 10
rawPath = '/URL Content/Raw Content'
cleanPath = '/URL Content/Clean Content'

def main():
    #Choose which instruction to do here
    #GetURLs()
    #GetContent()
    #CleanContent()
    #GetTerms()
    CombineSentences()
    GetFacts()

# Simple KB, to improve later
def GetFacts():
    # Open the file of important terms
    file = open(os.getcwd() + "\Important Terms Stemmed.txt", 'r', encoding='utf8')
    impTerms = file.read()
    impTerms = re.sub('[^\w]', ' ', impTerms).split()
    stemmer = SnowballStemmer('english')
    client = textrazor.TextRazor(extractors=["words", "entities", "entailments", "relations"])

    for term in impTerms:
        with open(os.getcwd() + '\Term Content\\' + term + '.txt', 'r', encoding='utf8') as f:
            with open(os.getcwd() + '\Term Content\Term Relations\\' + term + 'Relations.txt', 'w', encoding='utf8') as fNew:
                content = f.read()
                sent = word_tokenize(content)
                wordList = []
                wordString = ""
                for word in sent:
                    wordList.append(word)
                    wordString += word + " "
                newCont = client.analyze(wordString)
                for relation in newCont.relations():
                    for key, value in relation.json.items():
                        if key == 'params':
                            subjectFound = False
                            wordDict = {}
                            for rel in relation.json[key]:
                                subjectList = []
                                if rel['relation'] == 'SUBJECT':
                                    for word in rel['wordPositions']:
                                        if word < len(wordList):
                                            wordDict[word] = wordList[word]
                                            subjectList.append(wordList[word])
                                            if stemmer.stem(wordList[word]) == term:
                                                subjectFound = True
                                if subjectFound and rel['relation'] == 'SUBJECT':
                                    fNew.write(rel['relation'] + ' ')
                                    for word in subjectList:
                                        fNew.write(word + " ")
                                    fNew.write('\n')
                                    fNew.write("PREDICATE ")
                                    for pred in relation.predicate_positions:
                                        if pred < len(wordList):
                                            wordDict[pred] = wordList[pred]
                                            fNew.write(wordList[pred] + " ")
                                    fNew.write('\n')
                                if subjectFound and rel['relation'] == 'OBJECT':
                                    fNew.write(rel['relation'] + ' ')
                                    for word in rel['wordPositions']:
                                        if word < len(wordList):
                                            wordDict[word] = wordList[word]
                                            fNew.write(wordList[word] + " ")
                                    fNew.write('\n')
                                    subjectFound = False
                                    fNew.write("SENTENCE ")
                                    for k in sorted(wordDict):
                                        fNew.write(wordDict[k] + " ")
                                    fNew.write('\n')


def CombineSentences():
    file = open(os.getcwd() + "\Important Terms Stemmed.txt", 'r', encoding='utf8')
    impTerms = file.read()
    impTerms = re.sub('[^\w]', ' ', impTerms).split()
    stemmer = SnowballStemmer('english')
    for term in impTerms:
        with open(os.getcwd() + '\Term Content\\' + term + '.txt', 'w', encoding='utf8') as f:
            for fileName in os.listdir(os.getcwd() + cleanPath):
                file = open(os.getcwd() + cleanPath + '/' + fileName, 'r', encoding='utf8')
                content = file.read()
                content = sent_tokenize(content)
                for sentTokens in content:
                    wordTokens = word_tokenize(sentTokens)
                    for word in wordTokens:
                        if stemmer.stem(word) == term:
                            f.write(sentTokens + '\n')
                            break


def GetTerms():
    vocab = {}
    # Open each cleaned up file and format the content for tokenizing
    for fileName in os.listdir(os.getcwd() + cleanPath):
        file = open(os.getcwd() + cleanPath + '/' + fileName, 'r', encoding='utf8')
        content = file.read()
        content = content.lower()
        content = re.sub(r'[^\w\s]', '', content)
        content = word_tokenize(content)
        # Check if each word is a stop word, if not, add its value to the dictionary or increment
        for word in content:
            if word not in stopWords:
                if word in vocab:
                    vocab[word] += 1
                else:
                    vocab[word] = 1

    print('Top 50 Terms: ')
    index = 0
    for k in sorted(vocab, key=lambda k: vocab[k], reverse=True):
        if index > 50:
            break
        print('Term: ' + k + '        Amnt.: ' + vocab[k].__str__())
        index +=1

def CleanContent():
    # Open each content file
    for fileName in os.listdir(os.getcwd() + rawPath):
        file = open(os.getcwd() + rawPath + '/' + fileName, 'r', encoding='utf8')
        content = file.read()
        # Format and sentence tokenize
        content = re.sub(r'[\n'        ']', '', content)
        content = sent_tokenize(content, language='english')
        # Save formatted content to new file
        with open(os.getcwd() + cleanPath + '/' + fileName, 'w', encoding='utf8') as f:
            for sentence in content:
                tokens = word_tokenize(sentence)
                tokens = [w.lower() for w in tokens]
                table = str.maketrans('', '', string.punctuation)
                stripped = [w.translate(table) for w in tokens]
                words = [word for word in stripped if word.isalpha()]
                for word in words:
                    f.write(word + " ")
                f.write('.\n')

def GetContent():
    # Get Content
    linkIndex = 1
    with open('urls.txt', 'r') as f:
        for link in f:
            # Format the link
            link = link.replace('\n', '')
            # Do error checking on opening the links
            try:
                r = requests.get(link)
            except requests.exceptions.ConnectionError:
                print("Connection refused on: " + link)
                continue
            except requests.exceptions.TooManyRedirects:
                print("Too many redirects at: " + link)
                continue
            except requests.exceptions.RetryError:
                print("Too many redirects at: " + link)
                continue
            except requests.exceptions.ConnectTimeout:
                print("Timeout at: " + link)
                continue
            # Soup the link and save its contents to a file
            soup = BeautifulSoup(r.content, 'html.parser')
            text = soup.findAll('p')
            with io.open(os.getcwd() + rawPath + '/link' + linkIndex.__str__(), 'w', encoding='utf-8') as newF:
                for t in text:
                    newF.write(t.get_text() + '\n')
                newF.close()
            linkIndex += 1

def GetURLs():
    # Create queue for querying links
    linkQueue = starterURLs
    linkNum = 1
    # Get URLs
    with open('urls.txt', 'w') as f:
        # For all links in the link queue
        for l in linkQueue:
            # If the maximum number of links is reached, breal
            if linkNum >= MAX_LINKS:
                break
            # Get the link
            try:
                lonk = requests.get(l)
            except requests.exceptions.ConnectionError:
                print("Connection refused on: " + l)
                continue
            except requests.exceptions.TooManyRedirects:
                print("Too many redirects at: " + l)
                continue
            except requests.exceptions.RetryError:
                print("Too many redirects at: " + l)
                continue
            except requests.exceptions.ConnectTimeout:
                print("Timeout at: " + l)
                continue
            # Soup the link
            soup = BeautifulSoup(lonk.content, 'html.parser')
            linksOnPage = 0
            # Get URLs from link
            for link in soup.findAll('a'):
                # If max number of links for this page is reached, break
                if linksOnPage >= LINKS_PER_PAGE:
                    break
                # Format the URL
                linkStr = str(link.get("href"))
                if 'sustain' in linkStr or "Sustain" in linkStr:
                    if linkStr.startswith('/url?q='):
                        linkStr = linkStr[7:]
                    if '&' in linkStr:
                        i = linkStr.find('&')
                        linkStr = linkStr[:i]
                    if linkStr.startswith('http') and linkStr not in linkQueue:
                        include = True
                        # Check if URL contains a part of the notInclude list
                        for part in notInclude:
                            if part in linkStr:
                                include = False
                        if include:
                            # Add the URL and update values
                            f.write(linkStr + '\n')
                            linkQueue.append(linkStr)
                            linkNum += 1
                            linksOnPage += 1
    f.close()

if __name__ == "__main__":
    main()