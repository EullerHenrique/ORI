# Euller Henrique Bandeira Oliveira - 11821BSI210

import ssl
import nltk
import sys
import pickle

_create_unverified_https_context = ssl._create_unverified_context
ssl._create_default_https_context = _create_unverified_https_context

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('rslp')
nltk.download('mac_morpho')

stopwords = nltk.corpus.stopwords.words("portuguese")
stemmer = nltk.stem.RSLPStemmer()

etiquetador = ''
listaClasFin = []
d = dict()

try:

    arquivo = open('etiquetador.bin', 'rb')
    etiquetador = pickle.load(arquivo)

except FileNotFoundError:

    sentencas_etiquetadas = nltk.corpus.mac_morpho.tagged_sents()
    etiquetador = nltk.tag.UnigramTagger(sentencas_etiquetadas)
    arquivo = open('etiquetador.bin', 'wb')
    pickle.dump(etiquetador, arquivo)

arquivo.close()

arg = ''

for i, v in enumerate(sys.argv):
    if i == 1:
        arg = v

arqBase = open(arg, 'r')
textos = []

for linha in arqBase:
    v = linha.split()
    arq = open(v[0], encoding="utf8", mode='r')
    textos.append(arq.read())
    arq.close()

arqBase.close()

for idx, t in enumerate(textos):

    listaPalavrasFin = []

    frase = t
    listaPalavras = nltk.word_tokenize(frase)

    for i, val in enumerate(listaPalavras):
        listaPalavras[i] = val.lower()

    listaClas = []

    for p in listaPalavras:
        token = nltk.word_tokenize(p)
        classificacao = etiquetador.tag(token)
        listaClas.append(classificacao)

    listaClasStopword = []

    for t in listaClas:

        for (p, clas) in t:

            if clas == 'ART' or clas == 'PREP' or clas == 'KC' or clas == 'KS':
                listaClasStopword.append(p)

    itensRemocao = [".", "..", "...", "!", "?", ","]
    i = 0

    while i < len(listaPalavras):
        if listaPalavras[i] in itensRemocao or listaPalavras[i] in stopwords or listaPalavras[i] in listaClasStopword:
            listaPalavras.pop(i)
        else:
            i += 1

    for p in listaPalavras:
        token = nltk.word_tokenize(p)
        classificacao = etiquetador.tag(token)
        listaClasFin.append(classificacao)
        listaPalavrasFin.append(stemmer.stem(p))

    c = {}
    for p in listaPalavrasFin:
        if p not in c:
            c[p] = 0
        c[p] = c[p] + 1

    indice = idx + 1
    for p in c:
        if p in d:
            d[p].update({indice: c[p]})
        else:
            d[p] = {indice: c[p]}

for pc in listaClasFin:
    print(f"palavra - classificação: {pc}")
print()

d_sort = dict(sorted(d.items(), key=lambda item: item[0]))

for i in d_sort:
    print(i + ": ", end='')
    for ii in d_sort[i]:
        print(str(ii) + "," + str(d_sort[i][ii]) + " ", end='')
    print()

arq = open('indice.txt', encoding="utf8", mode='w')

for i in d_sort:
    arq.write(i + ":")
    for ii in d_sort[i]:
        arq.write(str(ii) + "," + str(d_sort[i][ii]) + " ")
    arq.write("\n")

arq.close()
