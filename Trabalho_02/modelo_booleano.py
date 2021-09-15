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

def indice_invertido():

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

    argBase = ''
    argConsulta = ''

    for i, v in enumerate(sys.argv):
        if i == 1:
            argBase = v
        if i == 2:
            argConsulta = v

    arqBase = open(argBase, 'r')
    textos = []
    docs = {}

    for i, linha in enumerate(arqBase):
        v = linha.split()
        docs.update({i + 1: v[0]})
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
            if listaPalavras[i] in itensRemocao or listaPalavras[i] in stopwords or listaPalavras[
                i] in listaClasStopword:
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

    return d_sort, docs, argConsulta


def modelo_booleano(d_sort, docs, argConsulta):
    arqConsulta = open(argConsulta, 'r')
    consulta = []

    for linha in arqConsulta:
        consulta = linha.split()
    arqConsulta.close()

    for i, val in enumerate(consulta):
        consulta[i] = val.lower()


    def procurarPalavra(palavra, ndoc):
        for i in d_sort:
            if stemmer.stem(palavra) == i:
                for ii in d_sort[i]:
                    if ii == ndoc:
                        return True
        return False

    resultsAll = {}

    palavra_sozinha = 1
    contAnd = 0

    # (!) palavra1 & (!) palavra2
    for i, val in enumerate(consulta):

        if val == '&':

            contAnd +=1

            for ndoc in range(1, len(docs) + 1):

                if consulta[i - 1][0] == '!':
                    p1 = not procurarPalavra(consulta[i - 1][1:], ndoc)
                else:
                    p1 = procurarPalavra(consulta[i - 1], ndoc)

                if consulta[i + 1][0] == '!':
                    p2 = not procurarPalavra(consulta[i + 1][1:], ndoc)
                else:
                    p2 = procurarPalavra(consulta[i + 1], ndoc)

                if p1 and p2:
                    pFinal = True
                else:
                    pFinal = False

                if ndoc in resultsAll:
                    resultsAll[ndoc].append(pFinal)
                else:
                    resultsAll[ndoc] = [pFinal]

            palavra_sozinha = 0

    # (!) palavra
    for i, val in enumerate(consulta):

        if palavra_sozinha == 1:

            for ndoc in range(1, len(docs) + 1):

                    if val[0] == '!':
                        p = procurarPalavra(val[1:], ndoc)
                        p = not p
                    else:
                        p = procurarPalavra(val, ndoc)

                    resultsAll.update({ndoc: [p]})

    for i, val in enumerate(consulta):

        for ndoc in range(1, len(docs) + 1):

            if val == '|':

                if len(resultsAll) != 0:

                    # a | b & c
                    if consulta[i - 2] != '&':

                        if consulta[i - 1][0] == '!':
                            p1 = not procurarPalavra(consulta[i - 1][1:], ndoc)
                        else:
                            p1 = procurarPalavra(consulta[i - 1], ndoc)

                        p2 = resultsAll[ndoc][-1]

                        if p1 or p2:
                            pFinal = True
                        else:
                            pFinal = False

                        if ndoc in resultsAll:
                            resultsAll[ndoc].append(pFinal)
                        else:
                            resultsAll[ndoc] = [pFinal]

                    # a & b | c
                    if len(consulta) - 2 == i:

                        if len(consulta) == 7:
                            p1 = resultsAll[ndoc][-2]
                        else:
                            p1 = resultsAll[ndoc][-1]

                        if consulta[i + 1][0] == '!':
                            p2 = not procurarPalavra(consulta[i + 1][1:], ndoc)
                        else:
                            p2 = procurarPalavra(consulta[i + 1], ndoc)

                        if p1 or p2:
                            pFinal = True
                        else:
                            pFinal = False

                        if ndoc in resultsAll:
                            resultsAll[ndoc].append(pFinal)
                        else:
                            resultsAll[ndoc] = [pFinal]

    for ndoc in range(1, len(docs) + 1):

        if len(consulta) > 3:

            p1 = resultsAll[ndoc][-1]
            p2 = resultsAll[ndoc][-2]

            if contAnd > 1:
                if p1 and p2:
                    pFinal = True
                else:
                    pFinal = False
            else:
                if p1 or p2:
                    pFinal = True
                else:
                    pFinal = False

            if ndoc in resultsAll:
                resultsAll[ndoc].append(pFinal)
            else:
                resultsAll[ndoc] = [pFinal]

    arq = open('resposta.txt', encoding="utf8", mode='w')

    cont = 0
    flagCont = 0

    for ndoc in resultsAll:
        if resultsAll[ndoc][-1]:
            cont += 1

    for ndoc in resultsAll:
        if resultsAll[ndoc][-1]:
            if flagCont == 0:
                print(cont)
                flagCont = 1
            print(docs[ndoc])

    flagCont = 0
    for ndoc in resultsAll:
        if resultsAll[ndoc][-1]:
            if flagCont == 0:
                arq.write(str(cont))
                arq.write("\n")
                flagCont = 1
            arq.write((docs[ndoc]))
            arq.write("\n")

    arq.close()
    print(resultsAll)

if __name__ == "__main__":
    d_sort, docs, argConsulta = indice_invertido()
    modelo_booleano(d_sort, docs, argConsulta)

