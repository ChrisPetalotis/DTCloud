from rdflib.plugins.sparql.processor import SPARQLResult
from typing import TypeVar

SPARQLEndpoint = TypeVar('SPARQLEndpoint', str, str)
filePath = TypeVar('filePath', str, str)


def getClassRelatedWords(text :str) -> list:
    import nltk
    import inflect
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    stop_words = set(nltk.corpus.stopwords.words('english'))
    stop_words.add("'s")
    p = inflect.engine()
    words = nltk.word_tokenize(text.lower())
    words = [word for word in words if word.isalpha()]
    words = [word for word in words if word not in stop_words]
    words = [p.singular_noun(word) or word for word in words]
    return words

def mapColumnToClass(column :str, classes :SPARQLResult, strict :bool = True, enhanced :bool = False) -> str:
    class_scores = {}
    winner = None
    for c in classes:
        if str(c[0].split('#')[-1]).lower() == column.lower():
            winner = c[0]
            break
        if str(c[0].split('/')[-1]).lower() == column.lower():
            winner = c[0]
            break
        if not strict:
            if not enhanced:
                if column.lower().endswith(str(c[0].split('#')[-1]).lower()):
                    winner = c[0]
                    break
                if column.lower().endswith(str(c[0].split('/')[-1]).lower()):
                    winner = c[0]
                    break
            else:
                if column.lower().replace("_", " ") == str(c[1]).lower():
                    winner = c[0]
                    break
                matching_score = 0
                column_words = column.split("_")
                for colword in column_words:
                    if c[1] != None:
                        label_words = getClassRelatedWords(str(c[1]))
                        for lword in label_words:
                            if lword == colword.lower():
                                matching_score += 100 * len(lword) * len(colword)
                            elif lword in colword.lower() or colword.lower() in lword:
                                matching_score += 10 * len(lword) * len(colword)
                            else:
                                matching_score -= 1
                    if c[2] != None:
                        comment_words = getClassRelatedWords(str(c[2]))
                        for cword in comment_words:
                            if cword in colword.lower() or colword.lower() in cword:
                                matching_score += 5
                class_scores[str(c[0])] = {"label":str(c[1]), "score": matching_score}
    if winner == None and strict == False and enhanced == True:
        maxScore = 0
        for cls, data in class_scores.items():
            if data['score'] > maxScore:
                winner = cls
                maxScore = data['score']
    return winner 

def mapInputToProperty(column :str, properties :SPARQLResult, strict :bool = True, enhanced :bool = False) -> str:
    prop_scores = {}
    winner = None
    for c in properties:
        if str(c[1].split('#')[-1]).lower() == column.lower():
            winner = c[1]
            break
        if str(c[1].split('/')[-1]).lower() == column.lower():
            winner = c[1]
            break
        if not strict:
            if not enhanced:
                if column.lower().endswith(str(c[1].split('#')[-1]).lower()):
                    winner = c[1]
                    break
                if column.lower().endswith(str(c[1].split('/')[-1]).lower()):
                    winner = c[1]
                    break
            else:
                if column.lower().replace("_", " ") == str(c[4]).lower():
                    winner = c[1]
                    break
                matching_score = 0
                column_words = column.split("_")
                for colword in column_words:
                    if c[4] != None:
                        label_words = getClassRelatedWords(str(c[4]))
                        for lword in label_words:
                            if lword == colword.lower():
                                matching_score += 100 * len(lword)
                            elif lword in colword.lower() or colword.lower() in lword:
                                matching_score += 10 * len(lword)
                            else:
                                matching_score -= 1
                    #matching_score *= len(colword)
                prop_scores[str(c[1])] = {"label":str(c[4]), "score": matching_score}
    if winner == None and strict == False and enhanced == True:
        maxScore = 0
        for prop, data in prop_scores.items():
            if data['score'] > maxScore:
                winner = prop
                maxScore = data['score']
    return winner

def mapInputToValue(column :str, properties :SPARQLResult, strict :bool = True) -> str:
    for c in properties:
        if c[0].lower() == column.lower():
            return c[1]
        elif not strict:
            if column.lower().endswith(c[0].lower()):
                return c[1]
            if column.lower() in c[0].lower():
                return c[1]
    return None

def mapContainerToService(container :str, services :SPARQLResult) -> str:
    scores = {}
    for s in services:
        score = 0
        for c in container.split('_'):
            if c.lower() in s['name'].lower():
                score += 10
            elif c.lower() in s['desc'].lower():
                score += 1
        scores[s['instance']] = score
    return max(scores, key=scores.get)

def findPropertyBasedOnDomainRangePair(properties, domain, range):
    for property in properties:
        try:
            if str(property[0]).split("#")[-1] == domain and str(property[2]).split("#")[-1] == range:
                p = property[1]
                return p
        except:
            pass
    return None