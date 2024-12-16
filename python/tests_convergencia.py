import time
import pandas as pd
import random

# Função para calcular o fitness de um indivíduo
def calcular_fitness(individuo, letras, palavras):
    print(f"Calculando fitness para indivíduo: {individuo}")
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

    print(f"Fitness calculado: {fitness}")
    return fitness

# Função para gerar uma população inicial
def gerar_populacao_inicial(tamanho, letras):
    print("Gerando população inicial...")
    populacao = []
    while len(populacao) < tamanho:
        individuo = random.sample(range(10), len(letras))  # Evita repetição de números
        populacao.append(individuo)
    print(f"População inicial gerada com {len(populacao)} indivíduos.")
    return populacao

# Função de mutação
def mutacao(individuo, taxa_mutacao):
    print(f"Mutando indivíduo: {individuo}")
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(individuo)), 2)
        individuo[i], individuo[j] = individuo[j], individuo[i]
        print(f"Indivíduo após mutação: {individuo}")
    return individuo

# Função de crossover cíclico
def crossover_ciclico(pai1, pai2):
    filho1 = pai1.copy()
    filho2 = pai2.copy()
    
    # Marcadores para saber quais genes já foram tratados
    visitados1 = [False] * len(pai1)
    visitados2 = [False] * len(pai2)
    
    i = 0
    while not all(visitados1):  # Continua até todos os genes de filho1 serem preenchidos
        if not visitados1[i]:
            # Preenche o gene do filho1 com o gene correspondente do pai2
            filho1[i] = pai2[i]
            visitados1[i] = True
            
            # Busca a próxima posição no ciclo
            i = pai1.index(filho1[i]) if filho1[i] in pai1 else (i + 1) % len(pai1)
        else:
            # Se o gene de filho1 já foi visitado, passa para o próximo
            i = (i + 1) % len(pai1)
    
    # Preenche os genes restantes do filho2
    for j in range(len(pai2)):
        if not visitados2[j]:
            filho2[j] = pai1[j]
    
    return filho1, filho2

# Função de crossover PMX
def crossover_pmx(pai1, pai2):
    print(f"Realizando crossover PMX entre pais: {pai1} e {pai2}")
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

    print(f"Filhos gerados: {filho1}, {filho2}")
    return filho1, filho2

# Função de crossover
def crossover(pai1, pai2, tipo_crossover):
    print(f"Realizando crossover do tipo {tipo_crossover}")
    if tipo_crossover == 'C1':
        return crossover_ciclico(pai1, pai2)
    elif tipo_crossover == 'C2':
        return crossover_pmx(pai1, pai2)
    else:
        raise ValueError(f"Tipo de crossover desconhecido: {tipo_crossover}")

# Função de seleção por roleta
def selecao_roleta(populacao, fitness):
    print("Selecionando pais por roleta...")
    total_fitness = sum([1 / (f + 1e-6) for f in fitness])  # Evitar divisão por zero
    chances = [1 / (f + 1e-6) / total_fitness for f in fitness]
    selecionados = random.choices(populacao, weights=chances, k=2)
    print(f"Pais selecionados: {selecionados}")
    return selecionados

# Função de seleção por torneio
def selecao_torneio(populacao, fitness, tamanho_torneio=3):
    print(f"Selecionando pais por torneio de tamanho {tamanho_torneio}...")
    pais = []
    for _ in range(2):
        torneio = random.sample(list(zip(populacao, fitness)), tamanho_torneio)
        pais.append(min(torneio, key=lambda x: x[1])[0])
    print(f"Pais selecionados: {pais}")
    return pais

# Função de algoritmo genético
def algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover, metodo_selecao):
    letras = list(set(''.join(palavras)))  # Obter as letras únicas
    print(f"Letras únicas encontradas: {letras}")
    populacao = gerar_populacao_inicial(tamanho_pop, letras)

    resultados = []
    for geracao in range(geracoes):
        print(f"Gerando nova geração {geracao}...")
        fitness = [calcular_fitness(individuo, letras, palavras) for individuo in populacao]
        melhor_fitness = min(fitness)
        print(f"Melhor fitness na geração {geracao}: {melhor_fitness}")

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
    #df.to_excel('resultados_ag.xlsx', index=False)

    return {'fitness': min(fitness), 'solucao': dict(zip(letras, melhor_individuo))}

# Função para registrar os resultados em um arquivo txt
def registrar_resultados_txt(resultados_completos, arquivo='resultados_ag.txt'):
    print(f"Registrando resultados em {arquivo}...")
    with open(arquivo, 'a') as f:
        for resultado in resultados_completos:
            f.write(f"Taxa de Crossover: {resultado['taxa_crossover']}\n")
            f.write(f"Taxa de Mutação: {resultado['taxa_mutacao']}\n")
            f.write(f"Tipo de Crossover: {resultado['tipo_crossover']}\n")
            f.write(f"Método de Seleção: {resultado['metodo_selecao']}\n")
            f.write(f"Fitness: {resultado['fitness']}\n")
            f.write(f"Solução: {resultado['solucao']}\n")
            f.write("-" * 50 + "\n")

# Função para executar múltiplas configurações
def executar_experimentos(palavras, geracoes, tamanho_pop, combinacoes_parametros):
    print("Executando experimentos...")
    resultados_completos = []

    for params in combinacoes_parametros:
        taxa_crossover, taxa_mutacao, tipo_crossover, metodo_selecao = params
        resultado_execucao = algoritmo_genetico(
            palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover, metodo_selecao
        )
        resultados_completos.append({
            'taxa_crossover': taxa_crossover,
            'taxa_mutacao': taxa_mutacao,
            'tipo_crossover': tipo_crossover,
            'metodo_selecao': metodo_selecao,
            'fitness': resultado_execucao['fitness'],
            'solucao': resultado_execucao['solucao']
        })

    df_resultados = pd.DataFrame(resultados_completos)
    df_resultados.to_excel('resultados_completos_ag.xlsx', index=False)

    registrar_resultados_txt(resultados_completos)

# Definindo as combinações de parâmetros
combinacoes_parametros = [
     (0.6, 0.05, 'C1', 'S1'),
    (0.6, 0.05, 'C1', 'S2'),
    (0.6, 0.05, 'C2', 'S1'),
    (0.6, 0.05, 'C2', 'S2'),
    (0.8, 0.05, 'C1', 'S1'),
    (0.8, 0.05, 'C1', 'S2'),
    (0.8, 0.05, 'C2', 'S1'),
    (0.8, 0.05, 'C2', 'S2'),
    (0.6, 0.1, 'C1', 'S1'),
    (0.6, 0.1, 'C1', 'S2'),
    (0.6, 0.1, 'C2', 'S1'),
    (0.6, 0.1, 'C2', 'S2'),
    (0.8, 0.1, 'C1', 'S1'),
    (0.8, 0.1, 'C1', 'S2'),
    (0.8, 0.1, 'C2', 'S1'),
    (0.8, 0.1, 'C2', 'S2')
]

# Definir as palavras a serem usadas no experimento
palavras = ['SEND', 'MORE', 'MONEY']

# Executando os experimentos
executar_experimentos(palavras, 50, 1000, combinacoes_parametros)
