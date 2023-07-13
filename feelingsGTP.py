
import openai

openai.api_key = "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"

# função para gerar uma resposta de um prompt
def get_completion(prompt, model="gpt-3.5-turbo"):

    # formatar o prompt como uma mensagem de usuário para a API de chat
    messages = [{"role": "user", "content": prompt}]

    # chamar a API de chat com o modelo especificado, as mensagens e a temperatura
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,  # este é o grau de aleatoriedade da saída do modelo
    )
    # retornar o conteúdo da resposta
    return response.choices[0].message["content"]

if __name__ == '__main__':

    frase = "Fiquei extremamente feliz pela minha promoção, " \
             "mas chateado porque meu amigo foi demitido. "

    frase = "{" + frase + "}"

    prompt = "Por favor, realize uma análise profunda e detalhada "\
             "do sentimento expresso na frase delimitada por {}, "\
             "classificando-a como positiva, negativa ou neutra. "\
             "Identifique e liste os sentimentos específicos presentes, "\
             "em sua forma mais simples e direta (palavra primitiva)" \
             "tanto explícitos quanto implícitos, e avalie a intensidade de cada sentimento de 0 (zero) a 100. "\
             "Indique quais palavras-chave na sentença contribuíram " \
             "para os sentimentos identificados. "\
             "Em seguida, sugira possíveis razões para esses sentimentos "\
             "com base no contexto da frase. Por fim, explique como você chegou " \
             "a essas conclusões. Retorne todas essas informações " \
             "no seguinte formato de um objeto JSON: " \
             "{" \
                "'classe': 'classe'," \
                "'sentimentos': {'sentimento': 'intensidade'}," \
                "'contribuicoes': {'palavra/frase': 'sentimento associado'}," \
                "'razoes_possiveis': ['string']," \
                "'explicacao_modelo': 'string'" \
            "}"


    prompt = prompt + "\n" + frase

    response = get_completion(prompt)

    print(response)