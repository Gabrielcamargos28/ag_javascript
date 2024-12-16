from flask import Flask, request, jsonify
import random
from flask_cors import CORS  

app = Flask(__name__)
CORS(app)

def calcular_fitness(individuo, letras, palavras):
    letter_to_digit = {letras[i]: individuo[i] for i in range(len(letras))}

    def palavra_para_numero(palavra):
        numero = ''.join([str(letter_to_digit[letra]) for letra in palavra])
        if numero[0] == '0': 
            return None
        return int(numero)


    valores_palavras = [palavra_para_numero(palavra) for palavra in palavras]
    if None in valores_palavras:
        return float('inf') 

    soma = sum(valores_palavras[:-1])
    resultado = valores_palavras[-1]
    return abs(soma - resultado)

def gerar_populacao_inicial(tamanho, letras):
    populacao = []
    while len(populacao) < tamanho:
        individuo = random.sample(range(10), len(letras))  
        populacao.append(individuo)
    return populacao

def mutacao(individuo, taxa_mutacao):
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(individuo)), 2)
        individuo[i], individuo[j] = individuo[j], individuo[i]
    return individuo

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

def crossover_pmx(pai1, pai2):
    size = len(pai1)
    filho1 = [-1] * size
    filho2 = [-1] * size
    
    ponto1, ponto2 = sorted(random.sample(range(size), 2))

    for i in range(ponto1, ponto2 + 1):
        filho1[i] = pai2[i]
        filho2[i] = pai1[i]
    
    def mapear(filho, pai, ponto1, ponto2):
        for i in range(size):
            if filho[i] == -1:
                gene = pai[i]
                while gene in filho:
                    gene = pai[filho.index(gene)]
                filho[i] = gene
    
    mapear(filho1, pai1, ponto1, ponto2)
    mapear(filho2, pai2, ponto1, ponto2)

    return filho1, filho2

def crossover(pai1, pai2, tipo_crossover):
    if tipo_crossover == 'C1':
        return crossover_ciclico(pai1, pai2)
    elif tipo_crossover == 'C2':
        return crossover_pmx(pai1, pai2)
    else:
        return crossover_ciclico(pai1, pai2) 


def algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover):
    letras = list(set(''.join(palavras))) 
    populacao = gerar_populacao_inicial(tamanho_pop, letras)

    melhor_fitness = float('inf')
    melhor_individuo = None

    for _ in range(geracoes):
        fitness = [calcular_fitness(individuo, letras, palavras) for individuo in populacao]
        
        
        fitness_atual = min(fitness)
        if fitness_atual < melhor_fitness: 
            melhor_fitness = fitness_atual
            melhor_individuo = populacao[fitness.index(melhor_fitness)]

        if melhor_fitness == 0:
            
            return dict(zip(letras, melhor_individuo)), melhor_fitness

        
        nova_populacao = []
        for _ in range(tamanho_pop // 2):
            pai1, pai2 = random.choices(populacao, weights=[1 / (f + 1e-6) for f in fitness], k=2)
            filho1, filho2 = crossover(pai1, pai2, tipo_crossover)
            nova_populacao.extend([mutacao(filho1, taxa_mutacao), mutacao(filho2, taxa_mutacao)])
        
        populacao = nova_populacao

    return dict(zip(letras, melhor_individuo)), melhor_fitness


@app.route('/solucao', methods=['POST'])
@app.route('/solucao', methods=['POST'])
def obter_solucao():
    data = request.get_json()
    palavras = data['palavras']
    geracoes = data['geracoes']
    tamanho_pop = data['tamanho_pop']
    taxa_crossover = data['taxa_crossover']
    taxa_mutacao = data['taxa_mutacao']
    tipo_crossover = data.get('tipo_crossover', 'C1') 

    solucao, melhor_fitness = algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover)

    
    return jsonify({
        'solucao': solucao,
        'melhor_fitness': melhor_fitness
    })


if __name__ == '__main__':
    app.run(debug=True)