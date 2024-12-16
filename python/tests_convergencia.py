import time
import pandas as pd
import random

# Função para calcular o fitness de um indivíduo
def calcular_fitness(individuo, letras, palavras):
    letter_to_digit = {letras[i]: individuo[i] for i in range(len(letras))}

    def palavra_para_numero(palavra):
        numero = ''.join([str(letter_to_digit[letra]) for letra in palavra])
        if numero[0] == '0':  # Não pode começar com zero
            return None
        return int(numero)

    valores_palavras = [palavra_para_numero(palavra) for palavra in palavras]
    if None in valores_palavras:
        return float('inf')  # Fitness alto se houver número inválido

    soma = sum(valores_palavras[:-1])
    resultado = valores_palavras[-1]
    fitness = abs(soma - resultado)

    return fitness

# Função para gerar uma população inicial
def gerar_populacao_inicial(tamanho, letras):
    populacao = []
    while len(populacao) < tamanho:
        individuo = random.sample(range(10), len(letras))  # Evita repetição de números
        populacao.append(individuo)
    return populacao

# Função de mutação
def mutacao(individuo, taxa_mutacao):
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(individuo)), 2)
        individuo[i], individuo[j] = individuo[j], individuo[i]
    return individuo

# Função de crossover cíclico
def crossover_ciclico(pai1, pai2):
    tamanho = len(pai1)
    filho1 = [-1] * tamanho
    filho2 = [-1] * tamanho

    ciclo = 0
    while -1 in filho1:
        inicio = filho1.index(-1)
        valor = pai1[inicio]
        while True:
            filho1[inicio] = pai1[inicio] if ciclo % 2 == 0 else pai2[inicio]
            filho2[inicio] = pai2[inicio] if ciclo % 2 == 0 else pai1[inicio]

            valor = pai2[inicio]
            try:
                inicio = pai1.index(valor)
            except ValueError:
                raise ValueError(f"Valor inesperado encontrado: {valor}. Verifique os pais para o crossover.")
            
            if valor == pai1[filho1.index(-1)]:
                break
        ciclo += 1

    return filho1, filho2

# Função de crossover PMX
def crossover_pmx(pai1, pai2):
    size = len(pai1)
    filho1 = [-1] * size
    filho2 = [-1] * size

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

# Função de crossover
def crossover(pai1, pai2, tipo_crossover):
    if tipo_crossover == 'C1':
        return crossover_ciclico(pai1, pai2)
    elif tipo_crossover == 'C2':
        return crossover_pmx(pai1, pai2)
    else:
        raise ValueError(f"Tipo de crossover desconhecido: {tipo_crossover}")

# Função de seleção por roleta
def selecao_roleta(populacao, fitness):
    total_fitness = sum([1 / (f + 1e-6) for f in fitness])  # Evitar divisão por zero
    chances = [1 / (f + 1e-6) / total_fitness for f in fitness]
    return random.choices(populacao, weights=chances, k=2)

# Função de seleção por torneio
def selecao_torneio(populacao, fitness, tamanho_torneio=3):
    pais = []
    for _ in range(2):
        torneio = random.sample(list(zip(populacao, fitness)), tamanho_torneio)
        pais.append(min(torneio, key=lambda x: x[1])[0])
    return pais

# Função de algoritmo genético
def algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover, metodo_selecao):
    letras = list(set(''.join(palavras)))  # Obter as letras únicas
    populacao = gerar_populacao_inicial(tamanho_pop, letras)

    resultados = []
    for geracao in range(geracoes):
        fitness = [calcular_fitness(individuo, letras, palavras) for individuo in populacao]
        melhor_fitness = min(fitness)

        if melhor_fitness == 0:
            melhor_individuo = populacao[fitness.index(melhor_fitness)]
            resultados.append({
                'geracao': geracao,
                'fitness': melhor_fitness,
                'solucao': dict(zip(letras, melhor_individuo))
            })
            return {'fitness': melhor_fitness, 'solucao': dict(zip(letras, melhor_individuo))}

        nova_populacao = []
        for _ in range(tamanho_pop // 2):
            if metodo_selecao == 'S1':
                pais = selecao_roleta(populacao, fitness)
            elif metodo_selecao == 'S2':
                pais = selecao_torneio(populacao, fitness)
            else:
                raise ValueError(f"Método de seleção desconhecido: {metodo_selecao}")
            
            filhos = crossover(pais[0], pais[1], tipo_crossover)
            nova_populacao.extend([mutacao(filhos[0], taxa_mutacao), mutacao(filhos[1], taxa_mutacao)])

        populacao = nova_populacao

    fitness = [calcular_fitness(individuo, letras, palavras) for individuo in populacao]
    melhor_individuo = populacao[fitness.index(min(fitness))]

    resultados.append({
        'geracao': geracoes,
        'fitness': min(fitness),
        'solucao': dict(zip(letras, melhor_individuo))
    })

    df = pd.DataFrame(resultados)
    df.to_excel('resultados_ag.xlsx', index=False)

    return {'fitness': min(fitness), 'solucao': dict(zip(letras, melhor_individuo))}

# Configurações e execução do AG
if __name__ == "__main__":
    palavras = ['SEND', 'MORE', 'MONEY']
    geracoes = 50
    tamanho_pop = 100
    taxa_crossover = 0.6
    taxa_mutacao = 0.05
    tipo_crossover = 'C1'
    metodo_selecao = 'S1'

    resultado = algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover, metodo_selecao)
    print("Resultado Final:", resultado)
