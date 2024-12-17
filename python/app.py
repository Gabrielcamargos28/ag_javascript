from flask import Flask, request, jsonify
import random
import time
from flask_cors import CORS
import pandas as pd  

app = Flask(__name__)
CORS(app)

# Fitness Function: |(SEND + MORE) - MONEY|
def calcular_fitness(individuo, letras, palavras):
    letter_to_digit = {letras[i]: individuo[i] for i in range(len(letras))}

    def palavra_para_numero(palavra):
        numero = ''
        for letra in palavra:
            if letra not in letter_to_digit:
                print(f"Erro: A letra {letra} não está mapeada para um número.")
                return None  # Ou pode retornar um valor especial
            numero += str(letter_to_digit[letra])
        return int(numero)

    valores_palavras = []
    for palavra in palavras:
        numero = palavra_para_numero(palavra)
        if numero is None:
            return float('inf')  # Caso algum erro aconteça na conversão

        valores_palavras.append(numero)

    soma = sum(valores_palavras[:-1])
    resultado = valores_palavras[-1]
    return abs(soma - resultado)


# População Inicial aleatória sem repetições
def gerar_populacao_inicial(tamanho, letras):
    if len(letras) > 10:
        raise ValueError(f"O número de letras ({len(letras)}) é maior do que o número de dígitos disponíveis (10).")
    populacao = []
    while len(populacao) < tamanho:
        individuo = random.sample(range(10), len(letras))
        populacao.append(individuo)
    return populacao

# Mutacao: Troca de 2 posições
def mutacao(individuo, taxa_mutacao):
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(individuo)), 2)
        individuo[i], individuo[j] = individuo[j], individuo[i]
    return individuo

# Crossover Ciclico (C1)
def crossover_ciclico(pai1, pai2):
    filho1 = pai1.copy()
    filho2 = pai2.copy()
    
    visitados1 = [False] * len(pai1)
    visitados2 = [False] * len(pai2)
    
    i = 0
    while not all(visitados1):  
        if not visitados1[i]:
            
            filho1[i] = pai2[i]
            visitados1[i] = True
            
            i = pai1.index(filho1[i]) if filho1[i] in pai1 else (i + 1) % len(pai1)
        else:

            i = (i + 1) % len(pai1)
    
    for j in range(len(pai2)):
        if not visitados2[j]:
            filho2[j] = pai1[j]
    
    return filho1, filho2

# Crossover PMX (C2)
def crossover_pmx(pai1, pai2):
    size = len(pai1)
    filho1, filho2 = [-1] * size, [-1] * size
    ponto1, ponto2 = sorted(random.sample(range(size), 2))

    for i in range(ponto1, ponto2 + 1):
        filho1[i] = pai2[i]
        filho2[i] = pai1[i]

    def mapear(filho, pai):
        for i in range(size):
            if filho[i] == -1:
                gene = pai[i]
                while gene in filho:
                    gene = pai[filho.index(gene)]
                filho[i] = gene

    mapear(filho1, pai1)
    mapear(filho2, pai2)
    return filho1, filho2

# Seleção: Roleta (S1) ou Torneio (S2)
def selecao_roleta(populacao, fitness):
    return random.choices(populacao, weights=[1 / (f + 1e-6) for f in fitness], k=2)

def selecao_torneio(populacao, fitness, k=3):
    torneio = random.sample(list(zip(populacao, fitness)), k)
    return [sorted(torneio, key=lambda x: x[1])[i][0] for i in range(2)]

# Reinserção: Ordenada (R1) ou Elitismo 20% (R2)
def reinsercao_ordenada(populacao, filhos, fitness, letras, palavras):
    populacao_total = populacao + filhos
    fitness_total = [calcular_fitness(ind, letras, palavras) for ind in populacao_total]
    return [ind for _, ind in sorted(zip(fitness_total, populacao_total))[:len(populacao)]]

def reinsercao_elitismo(populacao, filhos, fitness, letras, palavras):
    elitismo = 0.2
    elite_size = int(len(populacao) * elitismo)
    elite = sorted(populacao, key=lambda ind: calcular_fitness(ind, letras, palavras))[:elite_size]
    return elite + filhos[:len(populacao) - elite_size]

# Algoritmo Genético Principal
def algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, metodo_selecao, tipo_crossover, metodo_reinsercao):
    global letras
    letras = list(set(''.join(palavras)))
    populacao = gerar_populacao_inicial(tamanho_pop, letras)
    melhor_fitness, melhor_individuo = float('inf'), None
    geracao_melhor = 0
    
    for g in range(geracoes):
        fitness = [calcular_fitness(ind, letras, palavras) for ind in populacao]

        if metodo_selecao == 'S1':
            selecao = selecao_roleta
        else:
            selecao = lambda pop, fit: selecao_torneio(pop, fit, k=3)

        nova_populacao = []
        while len(nova_populacao) < tamanho_pop:
            pai1, pai2 = selecao(populacao, fitness)
            if random.random() < taxa_crossover:
                if tipo_crossover == 'C1':
                    filho1, filho2 = crossover_ciclico(pai1, pai2)
                else:
                    filho1, filho2 = crossover_pmx(pai1, pai2)
            else:
                filho1, filho2 = pai1.copy(), pai2.copy()
            nova_populacao.extend([mutacao(filho1, taxa_mutacao), mutacao(filho2, taxa_mutacao)])

        if metodo_reinsercao == 'R1':
            populacao = reinsercao_ordenada(populacao, nova_populacao, fitness, letras, palavras)
        else:
            populacao = reinsercao_elitismo(populacao, nova_populacao, fitness, letras, palavras)

        melhor_atual = min(fitness)
        if melhor_atual < melhor_fitness:
            melhor_fitness = melhor_atual
            melhor_individuo = populacao[fitness.index(melhor_fitness)]
            geracao_melhor = g
            
        if melhor_fitness == 0:
            break

    return dict(zip(letras, melhor_individuo)), melhor_fitness, geracao_melhor

@app.route('/solucao', methods=['POST'])
def obter_solucao():
    data = request.get_json()
    palavras = data['palavras']
    geracoes = data['geracoes']
    tamanho_pop = data['tamanho_pop']
    taxa_crossover = data['taxa_crossover']
    taxa_mutacao = data['taxa_mutacao']
    metodo_selecao = data['metodo_selecao']
    tipo_crossover = data['tipo_crossover']
    metodo_reinsercao = data['metodo_reinsercao']
    
    convergencia_encontrada = False
    num_execucoes = 0
    inicio = time.time()
    
    while not convergencia_encontrada and num_execucoes < 1000:  # Executar até achar a solução ou 1000 execuções
        num_execucoes += 1
        
        solucao, fitness, geracao_melhor = algoritmo_genetico(
            palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, 
            metodo_selecao, tipo_crossover, metodo_reinsercao
        )
        
        if fitness == 0:
            convergencia_encontrada = True

    fim = time.time()
    
    if not convergencia_encontrada:
        return jsonify({
            'erro': 'Não foi possível encontrar uma solução válida em 1000 execuções.'
        })
    
    return jsonify({
        'solucao': solucao,
        'fitness': fitness,
        'geracao_melhor': geracao_melhor,
        'tempo_execucao': fim - inicio,
        'num_execucoes': num_execucoes
    })


@app.route('/report', methods=['GET'])
def executar_testes():
    print("INICIANDO")
    # Primeira fase: Realizar 24 combinações e salvar resultados
    palavras = ['SEND', 'MORE', 'MONEY']
    geracoes = 50
    tamanho_pop = 100

    configuracoes = []
    resultados = []
    writer = pd.ExcelWriter('resultados_ag.xlsx', engine='xlsxwriter')  # Cria um writer para o Excel

    # Configurações de teste
    taxas_crossover = [0.6, 0.8]
    taxas_mutacao = [0.05, 0.1]
    metodos_selecao = ['S1', 'S2']
    tipos_crossover = ['C1', 'C2']
    metodos_reinsercao = ['R1', 'R2']

    for idx, (tc, tm, sel, cx, rein) in enumerate([
        (tc, tm, sel, cx, rein)
        for tc in taxas_crossover
        for tm in taxas_mutacao
        for sel in metodos_selecao
        for cx in tipos_crossover
        for rein in metodos_reinsercao
    ]):
        taxa_crossover = 0.8 if rein == 'R2' else tc

        configuracao = {
            'taxa_crossover': taxa_crossover,
            'taxa_mutacao': tm,
            'metodo_selecao': sel,
            'tipo_crossover': cx,
            'metodo_reinsercao': rein
        }
        configuracoes.append(configuracao)

        convergencias = 0
        tempos_execucao = []
        resultados_detalhados = []

        for i in range(1000):  # 1000 iterações por configuração
            print(f"Executando configuração {idx + 1}/24, iteração {i + 1}/1000")
            inicio = time.time()
            solucao, fitness, geracao_melhor = algoritmo_genetico(
                palavras, geracoes, tamanho_pop,
                taxa_crossover, tm, sel, cx, rein
            )
            fim = time.time()
            tempo_execucao_individual = fim - inicio
            tempos_execucao.append(tempo_execucao_individual)

            if fitness == 0:  # Solução válida
                convergencias += 1

            # Salva os resultados individuais
            resultado_individual = {
                'execucao': i + 1,
                'tempo_execucao': tempo_execucao_individual,
                'fitness': fitness,
                'solucao_valida': fitness == 0
            }
            resultados_detalhados.append(resultado_individual)

        # Persistindo os 1000 resultados individuais em uma aba separada
        df_detalhado = pd.DataFrame(resultados_detalhados)
        aba_nome = f'Config_{idx + 1}'  # Nome da aba no Excel
        df_detalhado.to_excel(writer, sheet_name=aba_nome, index=False)

        # Resumo da configuração
        tempo_medio = sum(tempos_execucao) / len(tempos_execucao)
        resultado = {
            'taxa_crossover': taxa_crossover,
            'taxa_mutacao': tm,
            'metodo_selecao': sel,
            'tipo_crossover': cx,
            'metodo_reinsercao': rein,
            'percentual_convergencia': (convergencias / 1000) * 100,
            'tempo_medio': tempo_medio
        }
        resultados.append(resultado)

    # Salva o resumo de todas as configurações em uma aba principal
    df_resumo = pd.DataFrame(resultados)
    df_resumo.to_excel(writer, sheet_name='Resumo_Configuracoes', index=False)

    writer.close()
    print("Resultados salvos no arquivo 'resultados_ag.xlsx'.")



    print("RESULTADOS MIL TESTES")

    problemas = [
        ['SEND', 'MORE', 'MONEY'],  
        ['PARA', 'AMAPA', 'GOIAS'], 
        ['CROSS', 'ROADS', 'DANGER'], 
        ['EAT', 'THAT', 'APPLE'], 
        ['DONALD', 'GERALD', 'ROBERT'],
        ['COCA', 'COLA', 'OASIS'],
    ]

    melhores_resultados = []

    for config in melhores_configuracoes:
        print("EXECUTANDO MELHORES 4 CONFIGURACOES")
        for palavras in problemas:
            convergencias = 0
            tempos_execucao = []
            for i in range(10):  # Correção: agora com um loop de 10 iterações por problema
                print(f"Executando iteração melhores configuracoes {i + 1}/10")
                inicio = time.time()
                solucao, fitness, geracao_melhor = algoritmo_genetico(
                    palavras, geracoes, tamanho_pop,
                    config['taxa_crossover'], config['taxa_mutacao'],
                    config['metodo_selecao'], config['tipo_crossover'],
                    config['metodo_reinsercao']
                )
                fim = time.time()
                tempo_execucao_individual = fim - inicio
                tempos_execucao.append(tempo_execucao_individual)

                if fitness == 0:  
                    convergencias += 1

            tempo_medio = sum(tempos_execucao) / len(tempos_execucao)
            resultado_final = {
                   'taxa_crossover': config['taxa_crossover'],
                   'taxa_mutacao': config['taxa_mutacao'],
                   'metodo_selecao': config['metodo_selecao'],
                   'tipo_crossover': config['tipo_crossover'],
                   'metodo_reinsercao': config['metodo_reinsercao'],
                   'percentual_convergencia': (convergencias / 5000) * 100,
                   'tempo_medio': tempo_medio,
                   'fitness': fitness,
                   'palavras': palavras,
                   'configuracao': configuracao
            }   
            melhores_resultados.append(resultado_final)

    
    melhores_resultados_ordenados = sorted(melhores_resultados, key=lambda x: (x['percentual_convergencia'], -x['tempo_medio']), reverse=True)

    
    print(melhores_resultados_ordenados)
    df_melhores = pd.DataFrame(melhores_resultados_ordenados)  # Agora salva todas as melhores configurações
    df_melhores.to_excel('melhores_resultados_ag.xlsx', index=False)

    print("\nResultados salvos no arquivo 'resultados_ag.xlsx' e 'melhores_resultados_ag.xlsx'.")


if __name__ == '__main__':
    #executar_testes()
    app.run(debug=True)
