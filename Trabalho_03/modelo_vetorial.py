# Euller Henrique Bandeira Oliveira - 11821BSI210

import ssl
import nltk
import sys
import pickle
import math

_create_unverified_https_context = ssl._create_unverified_context
ssl._create_default_https_context = _create_unverified_https_context

#nltk.download('stopwords')
#nltk.download('punkt')
#nltk.download('rslp')
#nltk.download('mac_morpho')

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

    print()
    print(d_sort)
    print()

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
        for p in d_sort:
            if stemmer.stem(palavra) == p:
                for nDoc in d_sort[p]:
                    if nDoc == ndoc:
                        return True
        return False

    resultsAll = {}

    palavra = 1
    contAnd = 0

    # (!) palavra1 & (!) palavra2
    for i, val in enumerate(consulta):

        if val == '&':

            contAnd += 1

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

            palavra = 0

    # (!) palavra
    for i, val in enumerate(consulta):

        if palavra == 1:

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

    cont = 0
    flagCont = 0

    for ndoc in resultsAll:
        if resultsAll[ndoc][-1]:
            cont += 1

    print(resultsAll)
    print()

    for ndoc in resultsAll:
        if resultsAll[ndoc][-1]:
            if flagCont == 0:
                print(cont)
                flagCont = 1
            print(docs[ndoc])

    print()

    flagCont = 0
    arq = open('resposta.txt', encoding="utf8", mode='w')
    for ndoc in resultsAll:
        if resultsAll[ndoc][-1]:
            if flagCont == 0:
                arq.write(str(cont))
                arq.write("\n")
                flagCont = 1
            arq.write((docs[ndoc]))
            arq.write("\n")
    arq.close()

def modelo_vetorial(d_sort, docs, argConsulta):

    arqConsulta = open(argConsulta, 'r')
    consulta = []

    for linha in arqConsulta:
        consulta = linha.split()
    arqConsulta.close()

    for i, val in enumerate(consulta):
        consulta[i] = val.lower()

    consulta_Freqs = {}
    for p in consulta:
        if p != '&':
            if p not in consulta_Freqs:
                consulta_Freqs[stemmer.stem(p)] = 0
            consulta_Freqs[stemmer.stem(p)] = consulta_Freqs[stemmer.stem(p)] + 1


    # Idfs dos documentos

    IDFs = {}

    for p in d_sort:
        # idf(A) = log(N/n_A)
        # N: qtd de documentos na base
        # n_A: qtd de docs com o termo A

        IDFs[p] = math.log(len(docs) / len(d_sort[p]), 10)

    print("\nIDFs\n")
    print(IDFs)

    # Pesos dos documentos
    Ws = {}

    for p in d_sort:

        for nDoc in d_sort[p]:
            # 1 + log(freq_A) * IDF_A
            Ws[(p, nDoc)] = (1 + math.log(d_sort[p][nDoc], 10)) * IDFs[p]

    print("\nWs\n")
    print(Ws)

    # Lista de pesos dos documentos
    Ds = {}
    for w in Ws:
        Ds[w[1]] = {}

    for w in Ws:
        if w[1] in Ds:
            Ds[w[1]].update({w[0]: Ws[w]})
        else:
            Ds[w[1]] = {w[0]: Ws[w]}

    Ds = dict(sorted(Ds.items(), key=lambda item: item[0]))

    print("\nDs\n")
    print(Ds)

    # Pesos da consulta
    DsC = {}

    # print(consulta_Freqs)

    for p in consulta_Freqs:
        # 1 + log(freq_A) * IDF_A
        DsC[p] = (1 + math.log(consulta_Freqs[p], 10)) * IDFs[p]

    print("\nDsC\n")
    print(DsC)

    # Similiraridades
    SimS = {}

    Calc_DS_DsC = {}
    Calc_Ds = {}
    Calc_DsC = 0

    for ndoc in range(1, len(docs) + 1):
        SimS[ndoc] = 0
        Calc_DS_DsC[ndoc] = 0
        Calc_Ds[ndoc] = 0

    for ndoc in range(1, len(docs) + 1):
        for pD in Ds:
            for pC in DsC:
                if pC in Ds[pD] and ndoc == pD:
                    Calc_DS_DsC[ndoc] += Ds[pD][pC] * DsC[pC]

    for ndoc in range(1, len(docs) + 1):
        for pD in Ds:
            if ndoc == pD:
                for p in Ds[pD]:
                    Calc_Ds[ndoc] += pow(Ds[pD][p], 2)

    arq = open('pesos.txt', encoding="utf8", mode='w')
    for ndoc in range(1, len(docs) + 1):
        arq.write(docs[ndoc] + ": ")
        for pD in Ds:
            if ndoc == pD:
                for p in Ds[pD]:
                    if Ds[pD][p] > 0:
                        arq.write(p + ", ")
                        arq.write(str(Ds[pD][p]))
                        arq.write("   ")
                arq.write("\n")
    arq.close()

    for pD in DsC:
        Calc_DsC += pow(DsC[pD], 2)

    for ndoc in range(1, len(docs) + 1):
        for pD in Ds:
            for pC in DsC:
                if pC in Ds[pD] and ndoc == pD:
                    SimS[ndoc] = (Calc_DS_DsC[ndoc]) / (math.sqrt(Calc_Ds[ndoc]) * math.sqrt(Calc_DsC))

    print("\nCalc_Ds_DsC\n")
    print(Calc_DS_DsC)

    print("\nCalcDs\n")
    print(Calc_Ds)

    print("\nCalcDsC\n")
    print(Calc_DsC)

    print("\nSimS\n")
    SimS = dict(sorted(SimS.items(), key=lambda item: item[1]))
    print(SimS)

    cont = 0
    for ndoc in SimS:
        if SimS[ndoc] >= 0.001:
            cont+=1

    flagCont = 0
    for ndoc in reversed(SimS):
        if SimS[ndoc] >= 0.001:
            if flagCont == 0:
                print("\n" + str(cont))
                flagCont = 1
            print(docs[ndoc] + " ", end="")
            print(str(SimS[ndoc]))

    flagCont = 0
    arq = open('resposta.txt', encoding="utf8", mode='w')
    for ndoc in reversed(SimS):
        if SimS[ndoc] >= 0.001:
            if flagCont == 0:
                arq.write(str(cont))
                arq.write("\n")
                flagCont = 1
            arq.write(docs[ndoc] + " ")
            arq.write(str(SimS[ndoc]))
            arq.write("\n")
    arq.close()

if __name__ == "__main__":
    d_sort, docs, argConsulta = indice_invertido()
    #modelo_booleano(d_sort, docs, argConsulta)
    modelo_vetorial(d_sort, docs, argConsulta)
