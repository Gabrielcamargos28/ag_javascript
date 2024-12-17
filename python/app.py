from flask import Flask, request, jsonify
import random
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Fitness Function: |(SEND + MORE) - MONEY|
def calcular_fitness(individuo, letras, palavras):
    letter_to_digit = {letras[i]: individuo[i] for i in range(len(letras))}

    def palavra_para_numero(palavra):
        numero = ''.join([str(letter_to_digit[letra]) for letra in palavra])
        return int(numero)

    try:
        valores_palavras = [palavra_para_numero(palavra) for palavra in palavras]
        soma = sum(valores_palavras[:-1])
        resultado = valores_palavras[-1]
        return abs(soma - resultado)
    except KeyError:  # Caso haja letras sem mapeamento
        return float('inf')

# População Inicial aleatória sem repetições
def gerar_populacao_inicial(tamanho, letras):
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
    
    for _ in range(geracoes):
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

    return dict(zip(letras, melhor_individuo)), melhor_fitness

# Endpoint principal
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

    inicio = time.time()
    solucao, fitness = algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, metodo_selecao, tipo_crossover, metodo_reinsercao)
    fim = time.time()

    return jsonify({
        'solucao': solucao,
        'fitness': fitness,
        'tempo_execucao': fim - inicio
    })


def executar_testes():
    palavras = ['SEND', 'MORE', 'MONEY']  # Problema base
    geracoes = 50
    tamanho_pop = 100

    configuracoes = []
    resultados = []

    # Combinações de parâmetros
    taxas_crossover = [0.6, 0.8]
    taxas_mutacao = [0.05, 0.1]
    metodos_selecao = ['S1', 'S2']  # Roleta (S1), Torneio (S2)
    tipos_crossover = ['C1', 'C2']  # Cíclico (C1), PMX (C2)
    metodos_reinsercao = ['R1', 'R2']  # Ordenada (R1), Elitismo (R2)

    # Loop por todas as 24 configurações
    for tc in taxas_crossover:
        for tm in taxas_mutacao:
            for sel in metodos_selecao:
                for cx in tipos_crossover:
                    for rein in metodos_reinsercao:
                        # Se reinserção for R2, taxa de crossover deve ser 0.8
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

                        # Executar 1000 vezes
                        for _ in range(1000):
                            inicio = time.time()
                            solucao, fitness = algoritmo_genetico(
                                palavras, geracoes, tamanho_pop,
                                taxa_crossover, tm, sel, cx, rein
                            )
                            fim = time.time()

                            # Verifica se solução válida foi encontrada
                            if fitness == 0:
                                convergencias += 1

                            tempos_execucao.append(fim - inicio)

                        # Armazena resultados
                        resultado = {
                            'configuracao': configuracao,
                            'percentual_convergencia': (convergencias / 1000) * 100,
                            'tempo_medio': sum(tempos_execucao) / len(tempos_execucao)
                        }
                        resultados.append(resultado)
                        print(f"Configuração: {configuracao} - Convergência: {resultado['percentual_convergencia']}% - Tempo Médio: {resultado['tempo_medio']:.2f} segundos")

    # Ordenar resultados por convergência e tempo
    resultados.sort(key=lambda x: (-x['percentual_convergencia'], x['tempo_medio']))

    # Exibir as 4 melhores configurações
    print("\nAs 4 melhores configurações:")
    for i in range(4):
        print(f"{i+1}. {resultados[i]['configuracao']} - Convergência: {resultados[i]['percentual_convergencia']}% - Tempo Médio: {resultados[i]['tempo_medio']:.2f} segundos")

    # Salvar em um arquivo (opcional)
    with open('resultados_ag.txt', 'w') as f:
        for r in resultados:
            f.write(f"{r}\n")

if __name__ == '__main__':
    executar_testes()



if __name__ == '__main__':
    app.run(debug=True)
